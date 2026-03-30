# =========================================================
# controller/main.py
# Interactive Control Layer v1
# =========================================================

import subprocess

def run_command(cmd):
    try:
        full_cmd = f"PYTHONPATH=. {cmd}"
        subprocess.run(full_cmd, shell=True)
#       subprocess.run(cmd, shell=True, check=True)
    except subprocess.CalledProcessError:
        print("❌ Error running:", cmd)


def choose_pool():
    print("\nSelect Pool:")
    print("1 Universe Pool")
    print("2 Watchlist Pool")

    choice = input("Enter (1/2): ")

    if choice == "1":
        return "universe"
    elif choice == "2":
        return "watchlist"
    else:
        print("Invalid choice, default = universe")
        return "universe"


def ask_yes_no(question):
    ans = input(f"{question} (y/n): ").lower()
    return ans == "y"


def main():

    print("🚀 Interactive Investment OS")

    # Step 1: Pool selection
    pool = choose_pool()
    print(f"✅ Selected pool: {pool}")

    # Step 2: Scanner
    if ask_yes_no("Run Scanner?"):
        print("📡 Running Scanner...")
        run_command(f"python3 scanner/basic_scanner.py {pool}")
    else:
        print("⏭ Skip Scanner")

    # Step 3: AI Narrative
    if ask_yes_no("Run AI Narrative input?"):
        print("🧠 Input AI Narrative...")
        run_command("PYTHONPATH=. python3 steps/input_narrative.py")
    else:
        print("⏭ Skip AI")

    # Step 4: Consensus
    if ask_yes_no("Run Consensus?"):
        print("🤝 Running Consensus...")
        run_command("PYTHONPATH=. python3 steps/consensus.py")
    else:
        print("⏭ Skip Consensus")

    # Step 5: Decision
    if ask_yes_no("Run Decision Engine?"):
        print("📊 Running Decision Engine...")
        run_command("PYTHONPATH=. python3 decision/decision_engine.py")
    else:
        print("⏭ Skip Decision")

    print("\n✅ Flow Completed")


if __name__ == "__main__":
    main()
