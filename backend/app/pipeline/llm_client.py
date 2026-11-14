import json
import logging
import os
import re
from typing import Optional, Dict, Any, Type, TypeVar
from pydantic import BaseModel
import anthropic
from backend.app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)

class LLMClient:
    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.ANTHROPIC_API_KEY
        self.model = model or settings.ANTHROPIC_MODEL
        self.mock_mode = (os.environ.get("MOCK_LLM", "").lower() in ("true", "1")) or settings.MOCK_LLM
        self._client = None
        if not self.mock_mode and self.api_key and self.api_key != "mock-anthropic-key":
            try:
                self._client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                logger.warning(f"Failed to initialize Anthropic client: {e}. Falling back to mock if needed.")

    def _extract_json_string(self, text: str) -> str:
        """Extract JSON content cleanly even if enclosed in markdown code fences."""
        text = text.strip()
        # Look for markdown code fence ```json ... ```
        fence_match = re.search(r"```(?:json)?\s*([\s\S]*?)\s*```", text)
        if fence_match:
            return fence_match.group(1).strip()
        # Look for first { to last }
        start = text.find("{")
        end = text.rfind("}")
        if start != -1 and end != -1 and end > start:
            return text[start:end+1]
        return text

    def generate(self, prompt: str, system: Optional[str] = None, max_tokens: int = 4000) -> str:
        """Raw LLM text completion."""
        if self.mock_mode or not self._client:
            return self._get_mock_raw_response(prompt)
        
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            system=system or "You are an elite competitive programming question author.",
            messages=[{"role": "user", "content": prompt}]
        )
        return response.content[0].text

    def generate_structured(
        self,
        prompt: str,
        schema: Type[T],
        system: Optional[str] = None,
        max_retries: int = 3
    ) -> T:
        """Generates LLM output, parses and validates against a Pydantic schema, retrying with error feedback."""
        current_prompt = prompt
        last_error = None

        for attempt in range(max_retries):
            raw_text = self.generate(current_prompt, system=system)
            json_str = self._extract_json_string(raw_text)
            try:
                data = json.loads(json_str)
                validated = schema.model_validate(data)
                return validated
            except Exception as e:
                last_error = f"Attempt {attempt+1} parse/validation error: {str(e)}"
                logger.warning(last_error)
                current_prompt = (
                    f"{prompt}\n\nCRITICAL FIX NEEDED:\n"
                    f"Your previous output failed validation with error:\n{str(e)}\n"
                    f"Raw output snippet: {json_str[:300]}\n"
                    f"Please correct the JSON and ensure it strictly matches the expected fields and types."
                )

        raise ValueError(f"Failed to generate structured data after {max_retries} attempts. Last error: {last_error}")

    def get_embedding(self, text: str) -> list[float]:
        """Generate a deterministic normalized pseudo-embedding or real vector embedding for dedup."""
        # For lightweight dedup without external vector APIs, produce a 64-dim normalized hash projection
        import hashlib
        import math
        tokens = re.findall(r"\w+", text.lower())
        vec = [0.0] * 64
        for t in tokens:
            h = int(hashlib.md5(t.encode("utf-8")).hexdigest(), 16)
            for i in range(64):
                if (h >> i) & 1:
                    vec[i] += 1.0
                else:
                    vec[i] -= 1.0
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [round(x / norm, 5) for x in vec]

    def _get_mock_raw_response(self, prompt: str) -> str:
        """Deterministic mock response for tests and local development without API keys."""
        if re.search(r"\b(critic|evaluation rubric|unambiguity)\b", prompt, re.IGNORECASE):
            return json.dumps({
                "scores": {
                    "clarity": 9.2,
                    "originality": 8.7,
                    "difficulty_match": 8.9,
                    "unambiguity": 9.0
                },
                "overall_score": 8.95,
                "passed": True,
                "critique": "Solid, original algorithmic challenge with crystal clear bounds and test invariants.",
                "suggested_improvements": ["Mention 0-indexed bounds explicitly in constraints."]
            })
        
        # Topic-aware distinct mock problem generator
        topic_match = re.search(r"Topic:\s*([^\n\r]+)", prompt)
        topic_str = topic_match.group(1).strip() if topic_match else "Arrays"
        import random
        rand_id = random.randint(100, 999999)

        if "graph" in topic_str.lower():
            title = f"Quantum Network Relay {rand_id}"
            story = f"A telecommunication network consists of N server nodes connected by bidirectional optical links with latency L. Find the minimum latency path."
            inp = "3 3\n1 2 4\n2 3 6\n1 3 15"
            tags = ["graphs", "dijkstra"]
        elif "greedy" in topic_str.lower():
            title = f"Resource Interval Allocation {rand_id}"
            story = f"Given N tasks with start time S and end time E, schedule the maximum number of non-overlapping tasks on a single machine."
            inp = "3\n1 3\n2 5\n4 6"
            tags = ["greedy", "intervals"]
        elif "dynamic" in topic_str.lower() or "dp" in topic_str.lower():
            title = f"Monolith Energy Subsequence {rand_id}"
            story = f"You are evaluating N energy monoliths where activating index i grants energy. You cannot activate consecutive monoliths. Maximize total power."
            inp = "4\n3 2 7 10"
            tags = ["dp", "subsequences"]
        else:
            title = f"Subarray Equilibrium Score {rand_id}"
            story = f"You are given an array of integers A of size N in {topic_str}. Compute the minimal equilibrium difference."
            inp = "1\n5\n1 2 3 4 5"
            tags = ["arrays", "prefix-sums"]

        return json.dumps({
            "title": title,
            "story": story,
            "input_format": "The first line contains testcase parameters.\nFollowed by space-separated elements.",
            "output_format": "Output a single integer representing the optimal result.",
            "constraints": "1 <= N <= 10^5\nAll values fit within 64-bit signed integers.",
            "sample_inputs": [
                "1\n5\n1 2 3 4 5",
                "1\n3\n2 0 2"
            ],
            "sample_outputs": [
                "1",
                "0"
            ],
            "explanation": "Walkthrough of sample inputs and outputs.",
            "tags": tags,
            "difficulty": "Medium",
            "time_limit": 2.0,
            "memory_limit": 256,
            "reference_solution": {
                "python": (
                    "import sys\n\n"
                    "def solve():\n"
                    "    lines = sys.stdin.read().split()\n"
                    "    if not lines:\n"
                    "        return\n"
                    "    T = int(lines[0])\n"
                    "    idx = 1\n"
                    "    out = []\n"
                    "    for _ in range(T):\n"
                    "        n = int(lines[idx])\n"
                    "        idx += 1\n"
                    "        arr = [int(x) for x in lines[idx:idx+n]]\n"
                    "        idx += n\n"
                    "        total = sum(arr)\n"
                    "        left = 0\n"
                    "        min_diff = float('inf')\n"
                    "        for x in arr:\n"
                    "            right = total - left - x\n"
                    "            diff = abs(left - right)\n"
                    "            if diff < min_diff:\n"
                    "                min_diff = diff\n"
                    "            left += x\n"
                    "        out.append(str(min_diff))\n"
                    "    sys.stdout.write('\\n'.join(out) + '\\n')\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                ),
                "java": (
                    "import java.io.*;\nimport java.util.*;\n\n"
                    "public class Solution {\n"
                    "    public static void main(String[] args) throws IOException {\n"
                    "        Scanner sc = new Scanner(System.in);\n"
                    "        if (!sc.hasNextInt()) return;\n"
                    "        int T = sc.nextInt();\n"
                    "        while (T-- > 0) {\n"
                    "            int n = sc.nextInt();\n"
                    "            long[] a = new long[n];\n"
                    "            long total = 0;\n"
                    "            for (int i=0; i<n; i++) { a[i] = sc.nextLong(); total += a[i]; }\n"
                    "            long left = 0, minDiff = Long.MAX_VALUE;\n"
                    "            for (int i=0; i<n; i++) {\n"
                    "                long right = total - left - a[i];\n"
                    "                long diff = Math.abs(left - right);\n"
                    "                if (diff < minDiff) minDiff = diff;\n"
                    "                left += a[i];\n"
                    "            }\n"
                    "            System.out.println(minDiff);\n"
                    "        }\n"
                    "    }\n"
                    "}\n"
                ),
                "cpp": (
                    "#include <bits/stdc++.h>\n"
                    "using namespace std;\n"
                    "int main() {\n"
                    "    ios_base::sync_with_stdio(false); cin.tie(NULL);\n"
                    "    int t;\n"
                    "    if (!(cin >> t)) return 0;\n"
                    "    while (t--) {\n"
                    "        int n;\n"
                    "        cin >> n;\n"
                    "        vector<long long> a(n);\n"
                    "        long long total = 0;\n"
                    "        for (int i=0; i<n; i++) { cin >> a[i]; total += a[i]; }\n"
                    "        long long left = 0, min_diff = LLONG_MAX;\n"
                    "        for (int i=0; i<n; i++) {\n"
                    "            long long right = total - left - a[i];\n"
                    "            long long diff = llabs(left - right);\n"
                    "            if (diff < min_diff) min_diff = diff;\n"
                    "            left += a[i];\n"
                    "        }\n"
                    "        cout << min_diff << \"\\n\";\n"
                    "    }\n"
                    "    return 0;\n"
                    "}\n"
                )
            },
            "brute_force_solution": (
                "import sys\n\n"
                "def solve():\n"
                "    lines = sys.stdin.read().split()\n"
                "    if not lines:\n"
                "        return\n"
                "    T = int(lines[0])\n"
                "    idx = 1\n"
                "    for _ in range(T):\n"
                "        n = int(lines[idx])\n"
                "        idx += 1\n"
                "        arr = [int(x) for x in lines[idx:idx+n]]\n"
                "        idx += n\n"
                "        best = float('inf')\n"
                "        for i in range(n):\n"
                "            left = sum(arr[:i])\n"
                "            right = sum(arr[i+1:])\n"
                "            best = min(best, abs(left - right))\n"
                "        print(best)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
            "test_case_generator_code": (
                "import random\n\n"
                "def generate():\n"
                "    cases = []\n"
                "    # Sample cases\n"
                "    cases.append('1\\n5\\n1 2 3 4 5')\n"
                "    cases.append('1\\n4\\n2 -1 3 0')\n"
                "    # Edge cases\n"
                "    cases.append('1\\n1\\n42')\n"
                "    cases.append('1\\n2\\n0 0')\n"
                "    cases.append('1\\n3\\n-1000 0 1000')\n"
                "    # Random cases\n"
                "    for size in [5, 10, 50, 100, 500, 1000, 5000]:\n"
                "        arr = [random.randint(-100, 100) for _ in range(size)]\n"
                "        cases.append(f'1\\n{size}\\n' + ' '.join(map(str, arr)))\n"
                "    for c in cases:\n"
                "        print('---TESTCASE---')\n"
                "        print(c.strip())\n\n"
                "if __name__ == '__main__':\n"
                "    generate()\n"
            ),
            "editorial": "By precomputing the sum of all elements, we can maintain the left running sum in O(1) per element and compute the right sum as total - left - A[i]. This eliminates the inner O(N) sum calculation, reducing total time complexity from O(N^2) to O(N) with O(1) auxiliary space."
        })
