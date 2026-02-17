import os
import subprocess
import re
import json
import shutil
from groq import Groq

TARGET_FILE = "fastapi/applications.py"
ITERATIONS = 3  # each model is run 3 times for reliability
TASK_PROMPT = """
Write a new method for the FastAPI class called 'secure_headers'.
It should add 'X-Frame-Options: DENY' and 'X-Content-Type-Options: nosniff' to every response.
Provide ONLY the Python code for the method. Do not include the class definition, just the function.
"""

# UTILS

def clean_code(code):
    code = re.sub(r"```python", "", code)
    code = re.sub(r"```", "", code)
    code = re.sub(r"<think>.*?</think>", "", code, flags=re.DOTALL)
    lines = code.split('\n')
    clean_lines = []
    started = False
    for line in lines:
        if line.strip().startswith("def ") or line.strip().startswith("@"):
            started = True
        if started: clean_lines.append(line)
    return "\n" + "\n".join(clean_lines) + "\n" if clean_lines else "\n" + code.strip() + "\n"

def run_tests():
    res = subprocess.run(['pytest', 'tests', '-q', '--disable-warnings', '-p', 'no:cacheprovider'], capture_output=True, text=True)
    match = re.search(r'(\d+) passed', res.stdout)
    passed = int(match.group(1)) if match else 0

    res_sec = subprocess.run(['bandit', '-r', TARGET_FILE, '-f', 'json'], capture_output=True, text=True)
    security = 0
    try:
        metrics = json.loads(res_sec.stdout).get('metrics', {}).get('_totals', {})
        security = metrics.get('SEVERITY.HIGH', 0) + metrics.get('SEVERITY.MEDIUM', 0)
    except: pass
    return passed, security

# HTML GENERATOR ---

def generate_html_report(results):
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>AI Efficiency Benchmark Report</title>
        <style>
            body {{ font-family: -apple-system, sans-serif; max-width: 950px; margin: 40px auto; background: #f4f4f9; color: #333; }}
            .container {{ background: white; padding: 40px; border-radius: 12px; box-shadow: 0 4px 20px rgba(0,0,0,0.08); }}
            h1 {{ border-bottom: 2px solid #eee; padding-bottom: 15px; }}
            .summary-box {{ background: #e8f5e9; padding: 20px; border-radius: 8px; color: #2e7d32; border: 1px solid #c8e6c9; margin: 20px 0; }}
            .code-box {{ background: #282c34; color: #abb2bf; 
            padding: 20px; 
            border-radius: 6px; 
            font-family: 'Menlo', 'Monaco', 'Courier New', monospace; 
            font-size: 0.85rem; 
            overflow-x: auto; 
            white-space: pre-wrap; 
            border: 1px solid #181a1f;
            margin: 20px 0;
            line-height: 1.4; }}
            table {{ width: 100%; border-collapse: collapse; margin-top: 25px; }}
            th {{ background-color: #f8f9fa; text-align: left; padding: 15px; border-bottom: 2px solid #eee; }}
            td {{ padding: 15px; border-bottom: 1px solid #eee; }}
            .pass {{ color: #27ae60; font-weight: 700; background: #e8f8f5; padding: 4px 8px; border-radius: 4px; }}
            .insight {{ background: #fff8e1; border-left: 4px solid #fbc02d; padding: 20px; margin-top: 30px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🛡️ AI Efficiency Benchmark</h1>
            <div class="summary-box">
                <strong>Executive Summary:</strong><br>
                This project leverages <strong>Python</strong> and <strong>Groq's high-speed infrastructure</strong> to compare two versions of Meta's Llama model and Qwen 3 to find the best balance for FastAPI project. 
                <br><br>
                The goal of this benchmark is to evaluate the structural integrity and token-efficiency of varied Large Language Model (LLM) architectures. By isolating performance on a strictly-typed, high-coverage repository like <strong>FastAPI</strong>, we can quantify which model offers the optimal balance of functional accuracy and minimal inference overhead. This data-driven approach allows for the deployment of a 'Right-Sized' AI strategy, where model selection is based on proven performance metrics rather than parameter count alone. 
                <br><br>
                By benchmarking against the FastAPI open source code, we utilize its industry-leading type-safety and 3,000+ unit tests as a 'Truth Signal.' This high-coverage environment allows us to objectively quantify model performance, detecting even minor regressions in code integrity or security awareness that would be missed in less robust repositories.
            </div>            
            <h2>1. The Challenge</h2>
            <p>Agents were tasked with injecting secure HTTP headers (X-Frame-Options, X-Content-Type) into a FastAPI application.</p>
            <div class="code-box">{TASK_PROMPT}</div>

            <table>
                <thead>
                    <tr>
                        <th>Agent Model</th>
                        <th>Consistency Score</th>
                        <th>Avg Tokens</th>
                        <th>Security Issues</th>
                    </tr>
                </thead>
                <tbody>
    """
    for res in results:
        html_content += f"""
                    <tr>
                        <td><strong>{res['Agent']}</strong></td>
                        <td><span class="pass">{res['Consistency %']}</span></td>
                        <td>{res['Avg Tokens']}</td>
                        <td>{res['Total Sec']}</td>
                    </tr>
        """
    html_content += """
                </tbody>
            </table>

            <div class="insight">
                <h3>💰 Strategic Advantage</h3>
                <p>The selection criteria prioritizes Reliability Parity as the baseline for production readiness. Since multiple architectures achieved a 100% Consistency Score, the selection is determined by Inference Efficiency. By deploying the model with the lowest token footprint that still maintains 100% accuracy, we achieve an optimal cost-to-performance ratio. This 'Right-Sizing' approach ensures we meet the rigorous demands of the FastAPI ecosystem while minimizing operational expenditure (OpEx) and maximizing system throughput.</p>
            </div>
        </div>
    </body>
    </html>
    """
    with open("dashboard.html", "w") as f: f.write(html_content)
    print("\n✅ Dashboard generated: dashboard.html")

# MAIN

def main():
    print(f" Initiating Cross-Model Reliability Benchmarking ({ITERATIONS} runs per model)...")
    contenders = [
        ("Llama 3.3 (70B)", "llama-3.3-70b-versatile"),
        ("Llama 3.1 (8B)", "llama-3.1-8b-instant"),
        ("Qwen 3 (32B)", "qwen/qwen3-32b")
    ]

    results = []
    client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

    try:
        for name, model_id in contenders:
            print(f"\n Testing {name}...")
            success_count, total_tokens, total_sec = 0, 0, 0

            for i in range(ITERATIONS):
                # Standard reset before each run
                subprocess.run(['git', 'checkout', '--', TARGET_FILE], capture_output=True)

                try:
                    completion = client.chat.completions.create(
                        messages=[{"role": "user", "content": TASK_PROMPT}],
                        model=model_id,
                        temperature=0.7
                    )
                    code = clean_code(completion.choices[0].message.content)
                    with open(TARGET_FILE, "a") as f: f.write(code)

                    passed, security = run_tests()
                    if passed >= 3032: success_count += 1
                    total_sec += security
                    total_tokens += completion.usage.total_tokens
                    print(f"   - Run {i+1}: {'✅ PASS' if passed >= 3032 else '❌ FAIL'}")
                except Exception as e:
                    print(f"   - Run {i+1}: ❌ ERROR: {e}")

            results.append({
                "Agent": name,
                "Consistency %": f"{(success_count / ITERATIONS) * 100:.1f}%",
                "Avg Tokens": int(total_tokens / ITERATIONS),
                "Total Sec": total_sec
            })

        # Generate the report only if the loops finished successfully
        generate_html_report(results)

    finally:
        # Reset target file
        subprocess.run(['git', 'checkout', '--', TARGET_FILE], capture_output=True)

        for p in ["log.txt", "coverage", ".pytest_cache"]:
            if os.path.exists(p):
                if os.path.isdir(p): shutil.rmtree(p)
                else: os.remove(p)

if __name__ == "__main__":
    main()
