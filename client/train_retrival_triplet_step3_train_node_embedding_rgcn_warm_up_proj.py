#!/usr/bin/env python
# Enhanced R-GCN Training with Triplet, InfoNCE, and Structure Loss + Validation + Best Model Save

import json, math, random, torch
import torch.nn.functional as F
from tqdm import tqdm
from pathlib import Path
from torch_geometric.loader import DataLoader as PyGDL
from torch_geometric.data import InMemoryDataset
from torch_geometric.data.storage import BaseStorage
from torch_geometric.nn import RGCNConv
from sklearn.model_selection import train_test_split

# ───── Configuration ─────
IN_DIM = 384; HIDDEN = 512; OUT_DIM = 384
NUM_BASES = 30; HOP = 1; SELF_WEIGHT = 0.8
EPOCHS = 100; START_TRIPLET_EPOCH = 5
BATCH = 4; LR = 5e-4; TEMP = 0.05; MARGIN = 0.5; MAX_TRIPLETS = 256
VAL_RATIO = 0.1

DATA_DIR = Path("cache/cached_graphs_dummy_embed_fixed_from_string_ver1+2")
EDGE_MAP_PATH = Path("config/graph/edge_type_map.json")
SAVE_DIR = Path("model/embed_triplet_struct_ver1+2")
SAVE_DIR.mkdir(parents=True, exist_ok=True)
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ───── Dataset ─────
class InMemorySceneDataset(InMemoryDataset):
    def __init__(self, root):
        super().__init__(root)
        self.data_list = [torch.load(p, map_location="cpu", weights_only=False)['data']
                          for p in sorted(root.rglob("*.pt"))
                          if p.name != "unique_texts.pt"]
    def __len__(self): return len(self.data_list)
    def __getitem__(self, i): return self.data_list[i]

# ───── Model ─────
class RGCN(torch.nn.Module):
    def __init__(self, num_rel):
        super().__init__()
        self.self_loop_id = num_rel
        self.convs = torch.nn.ModuleList([
            RGCNConv(IN_DIM if i == 0 else HIDDEN,
                     OUT_DIM if i == HOP - 1 else HIDDEN,
                     num_rel + 1, num_bases=NUM_BASES)
            for i in range(HOP)])

    def forward(self, x, edge_index, edge_type):
        N = x.size(0)
        loop_idx = torch.arange(N, device=x.device)
        self_loops = torch.stack([loop_idx, loop_idx])
        loop_types = torch.full((N,), self.self_loop_id, dtype=torch.long, device=x.device)
        edge_index = torch.cat([edge_index, self_loops], dim=1)
        edge_type  = torch.cat([edge_type, loop_types])
        out = x
        for i, conv in enumerate(self.convs):
            h = conv(out, edge_index, edge_type)
            out = SELF_WEIGHT * out + (1 - SELF_WEIGHT) * (F.relu(h) if i < HOP - 1 else h)
        return out

# ───── Losses ─────
def _norm(t): return F.normalize(t, dim=1)

def info_nce(z, e, temp=TEMP):
    z, e = _norm(z), _norm(e)
    sim = z @ e.T / temp
    target = torch.arange(z.size(0), device=z.device)
    return F.cross_entropy(sim, target)

def structure_loss(z, edge_index):
    src, dst = edge_index
    pos_score = (z[src] * z[dst]).sum(dim=1)
    neg_dst = dst[torch.randperm(dst.size(0))]
    neg_score = (z[src] * z[neg_dst]).sum(dim=1)
    return F.binary_cross_entropy_with_logits(torch.cat([pos_score, neg_score]),
                                              torch.cat([torch.ones_like(pos_score), torch.zeros_like(neg_score)]))

def embedding_triplet_loss(z, node_type, target_type, name="(unknown)", margin=0.5, debug=True):
    idx = torch.nonzero(node_type == target_type).flatten()
    if idx.numel() < 2:
        return torch.tensor(0.0, device=z.device)
    emb = F.normalize(z[idx], dim=1)
    sim = emb @ emb.T
    μ, σ = sim.mean().item(), sim.std().item()
    POS = min(μ + σ, 0.7); NEG = max(μ - σ, 0.2)
    anchors, pos, neg = [], [], []
    for i in range(len(idx)):
        a = idx[i].item()
        sims = sim[i]; sims[i] = -1
        pos_cands = (sims >= POS).nonzero(as_tuple=True)[0]
        neg_cands = (sims <= NEG).nonzero(as_tuple=True)[0]
        if len(pos_cands) == 0 or len(neg_cands) == 0: continue
        p = idx[pos_cands[0].item()].item()
        n = idx[neg_cands[0].item()].item()
        anchors.append(a); pos.append(p); neg.append(n)
        if len(anchors) >= MAX_TRIPLETS: break
    if not anchors:
        return torch.tensor(0.0, device=z.device)
    a, p, n = map(lambda x: torch.tensor(x, device=z.device), (anchors, pos, neg))
    dist_ap = (z[a] - z[p]).pow(2).sum(1)
    dist_an = (z[a] - z[n]).pow(2).sum(1)
    return F.relu(dist_ap - dist_an + margin).mean()

# ───── Training Loop ─────
def train():
    with EDGE_MAP_PATH.open() as f:
        num_rel = len(json.load(f))
    full_dataset = InMemorySceneDataset(DATA_DIR)
    indices = list(range(len(full_dataset)))
    train_idx, val_idx = train_test_split(indices, test_size=VAL_RATIO, random_state=42)
    train_ds = torch.utils.data.Subset(full_dataset, train_idx)
    val_ds   = torch.utils.data.Subset(full_dataset, val_idx)
    train_loader = PyGDL(train_ds, batch_size=BATCH, shuffle=True, num_workers=4, pin_memory=True)
    val_loader   = PyGDL(val_ds, batch_size=BATCH, shuffle=False, num_workers=4, pin_memory=True)

    model = RGCN(num_rel).to(DEVICE)
    opt = torch.optim.Adam(model.parameters(), lr=LR)
    best_val_loss = float('inf')

    for ep in range(1, EPOCHS + 1):
        model.train(); total_loss = 0.0
        for batch in tqdm(train_loader, desc=f"[Train] {ep:03d}", leave=False):
            batch = batch.to(DEVICE); opt.zero_grad(set_to_none=True)
            x, ei, et, nt = batch.x, batch.edge_index, batch.edge_type, batch.node_type
            z = model(x, ei, et); e = batch.x.detach()
            l_align = info_nce(z, e)
            l_trip_obj = embedding_triplet_loss(z, nt, 1, name="object") if ep >= START_TRIPLET_EPOCH else torch.tensor(0.0, device=DEVICE)
            l_trip_evt = embedding_triplet_loss(z, nt, 2, name="event")  if ep >= START_TRIPLET_EPOCH else torch.tensor(0.0, device=DEVICE)
            l_trip_spt = embedding_triplet_loss(z, nt, 3, name="spatial") if ep >= START_TRIPLET_EPOCH else torch.tensor(0.0, device=DEVICE)
            l_trip = l_trip_obj + l_trip_evt + l_trip_spt
            l_struct = structure_loss(z, ei)
            loss = l_align + 0.5 * l_trip + 1.0 * l_struct
            loss.backward(); opt.step(); total_loss += loss.item()

        model.eval(); val_loss = 0.0
        with torch.no_grad():
            for batch in val_loader:
                batch = batch.to(DEVICE)
                x, ei, et, nt = batch.x, batch.edge_index, batch.edge_type, batch.node_type
                z = model(x, ei, et); e = batch.x
                l_align = info_nce(z, e)
                l_trip_obj = embedding_triplet_loss(z, nt, 1)
                l_trip_evt = embedding_triplet_loss(z, nt, 2)
                l_trip_spt = embedding_triplet_loss(z, nt, 3)
                l_trip = l_trip_obj + l_trip_evt + l_trip_spt
                l_struct = structure_loss(z, ei)
                loss = l_align + 0.5 * l_trip + 1.0 * l_struct
                val_loss += loss.item()
        val_loss /= len(val_loader)

        print(f"Epoch {ep:03d} | train={total_loss / len(train_loader):.4f} | val={val_loss:.4f} | align={l_align:.4f} | trip={l_trip:.4f} ({l_trip_obj:.4f}, {l_trip_evt:.4f}, {l_trip_spt:.4f}) | struct={l_struct:.4f}")
        if val_loss < best_val_loss:
            print(f"  🏆 New best validation loss: {val_loss:.4f}, saving model...")
            best_val_loss = val_loss
            torch.save(model.state_dict(), SAVE_DIR / "best_model.pt")
    print("✅ Training complete.")

if __name__ == "__main__":
    train()
