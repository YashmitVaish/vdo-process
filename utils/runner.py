import subprocess

def run_command(command):
    try:
        result = subprocess.run(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        if result.returncode != 0:
            print("Error:", result.stderr)
        else:
            print("Success")

        return result
    except Exception as e:
        print("Execution failed:", e)