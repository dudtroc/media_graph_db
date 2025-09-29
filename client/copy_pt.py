import os
import shutil

def copy_pt_files(src_dir: str, dst_dir: str):
    """
    src_dir 하위(재귀적으로) 모든 .pt 파일을 찾아 dst_dir로 복사합니다.
    파일 이름은 그대로 유지하며, 동일 이름이 있으면 덮어씁니다.
    """
    os.makedirs(dst_dir, exist_ok=True)

    for root, _, files in os.walk(src_dir):
        for file in files:
            if file.lower().endswith(".pt"):  # .pt 확장자만 찾음
                src_path = os.path.join(root, file)
                dst_path = os.path.join(dst_dir, file)

                shutil.copy2(src_path, dst_path)  # 덮어쓰기
                print(f"Copied: {src_path} -> {dst_path}")
# 예시 실행
if __name__ == "__main__":
    source_directory = "/home/ktva/PROJECT/Diffusion/GP_adapter/cache/cached_graphs_drama_media_data_embed_fixed_from_string"   # JSON 파일이 있는 디렉토리
    target_directory = "./data2"   # 복사할 디렉토리
    copy_pt_files(source_directory, target_directory)
