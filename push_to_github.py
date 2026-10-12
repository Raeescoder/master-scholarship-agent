import sys
import os
import argparse
from urllib.parse import urlparse, urlunparse
from dulwich import porcelain
from dulwich.repo import Repo

def push_to_github(repo_url: str, token: str = None, username: str = None, branch: str = "main"):
    repo_path = os.path.abspath(os.path.dirname(__file__))
    print(f"[*] Preparing repository at: {repo_path}")
    
    # Clean and format remote URL
    repo_url = repo_url.strip()
    if not repo_url.endswith(".git"):
        repo_url += ".git"

    # If token is provided, embed in authenticated HTTPS URL
    parsed = urlparse(repo_url)
    if token:
        if username:
            auth_netloc = f"{username}:{token}@{parsed.hostname}"
        else:
            auth_netloc = f"{token}@{parsed.hostname}"
        if parsed.port:
            auth_netloc += f":{parsed.port}"
        authenticated_url = urlunparse((parsed.scheme, auth_netloc, parsed.path, parsed.params, parsed.query, parsed.fragment))
    else:
        authenticated_url = repo_url

    print(f"[*] Pushing branch '{branch}' to {parsed.netloc}{parsed.path} ...")
    try:
        r = Repo(repo_path)
        refspec = f"refs/heads/{branch}:refs/heads/{branch}".encode("utf-8")
        
        # Add remote if not already present
        try:
            porcelain.remote_add(r, "origin", repo_url)
            print("[*] Configured remote 'origin'.")
        except Exception:
            pass

        # Push to remote
        result = porcelain.push(r, authenticated_url, refspecs=[refspec])
        print("\n[SUCCESS] Successfully pushed repository to GitHub!")
        print(f"[*] View your code at: https://github.com{parsed.path.removesuffix('.git')}")
        return True
    except Exception as e:
        print(f"\n[ERROR] Push failed: {e}")
        print("\nTip: Make sure:")
        print("1. The repository exists on your GitHub account (create it at https://github.com/new).")
        print("2. Your GitHub Personal Access Token (PAT) has the 'repo' scope permission.")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Push ScholarAI repository to GitHub.")
    parser.add_argument("--repo", help="GitHub repository URL (e.g. https://github.com/username/scholarai.git)")
    parser.add_argument("--token", help="GitHub Personal Access Token (classic or fine-grained with repo access)")
    parser.add_argument("--user", help="GitHub username (optional)")
    parser.add_argument("--branch", default="main", help="Target branch name (default: main)")

    args = parser.parse_args()

    repo_url = args.repo
    token = args.token
    user = args.user

    if not repo_url:
        print("=" * 60)
        print(" 🚀 ScholarAI GitHub Push Helper")
        print("=" * 60)
        repo_url = input("Enter GitHub repository URL (e.g. https://github.com/username/scholarai.git): ").strip()
    
    if not token and not repo_url.startswith("git@"):
        token = input("Enter GitHub Personal Access Token (PAT): ").strip()

    if repo_url:
        push_to_github(repo_url, token=token, username=user, branch=args.branch)
    else:
        print("[!] No repository URL provided.")
