#!/usr/bin/env python3

import os
import sys
import argparse
from huggingface_hub import HfApi


def main():
    parser = argparse.ArgumentParser(
        description="Upload a local folder of images as a Hugging Face dataset"
    )
    parser.add_argument(
        "--folder_path",
        required=True,
        help="Local path to the folder containing your images",
    )
    parser.add_argument(
        "--repo_id",
        # default="imageomics/beetle-intake",
        help="Hugging Face repo ID (e.g. user_or_org/repo_name)",
    )
    parser.add_argument(
        "--repo_type",
        default="dataset",
        help="Type of repo: dataset or model",
    )
    parser.add_argument(
        "--path_in_repo",
        default="images",
        help="Sub‐folder inside the dataset repo where files will live",
    )
    parser.add_argument(
        "--branch",
        default="main",
        help="Branch name to upload to (default: main)",
    )
    args = parser.parse_args()

    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        print("Error: HF_TOKEN environment variable not set.", file=sys.stderr)
        sys.exit(1)

    api = HfApi(token=hf_token)

    # Create branch if it doesn't exist (only if not main)
    if args.branch != "main":
        try:
            print(f"Checking if branch '{args.branch}' exists...")
            api.repo_info(repo_id=args.repo_id, repo_type=args.repo_type, revision=args.branch)
            print(f"Branch '{args.branch}' exists.")
        except Exception:
            print(f"Branch '{args.branch}' doesn't exist. Creating it...")
            api.create_branch(
                repo_id=args.repo_id,
                branch=args.branch,
                repo_type=args.repo_type,
                exist_ok=True
            )
            print(f"Branch '{args.branch}' created successfully.")

    print(f"Uploading folder {args.folder_path} to {args.repo_id} ({args.repo_type}) on branch '{args.branch}'…")
    api.upload_folder(
        folder_path=args.folder_path,
        repo_id=args.repo_id,
        repo_type=args.repo_type,
        path_in_repo=args.path_in_repo,
        revision=args.branch,
    )
    print("Upload complete.")


if __name__ == "__main__":
    main()