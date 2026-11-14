import logging
from sqlalchemy.orm import Session
from backend.app.models import User, UserRole, DifficultyRubric, Question, TestCase, QuestionStatus
from backend.app.auth import get_password_hash

logger = logging.getLogger(__name__)

def seed_initial_data(db: Session):
    # 1. Seed Users (Admin & Reviewer)
    admin = db.query(User).filter(User.email == "admin@questforge.io").first()
    if not admin:
        admin = User(
            email="admin@questforge.io",
            hashed_password=get_password_hash("admin123"),
            role=UserRole.ADMIN.value,
            is_active=True
        )
        db.add(admin)

    reviewer = db.query(User).filter(User.email == "reviewer@questforge.io").first()
    if not reviewer:
        reviewer = User(
            email="reviewer@questforge.io",
            hashed_password=get_password_hash("reviewer123"),
            role=UserRole.REVIEWER.value,
            is_active=True
        )
        db.add(reviewer)

    # 2. Seed Difficulty Rubrics
    rubrics = [
        {
            "difficulty": "Easy",
            "max_solution_lines": 20,
            "time_complexity_target": "O(N)",
            "concepts_count": 1,
            "constraints_guideline": "1 <= N <= 10^4, simple simulation or two-pointers",
            "description": "Single concept, straightforward implementation with minimal edge cases."
        },
        {
            "difficulty": "Medium",
            "max_solution_lines": 40,
            "time_complexity_target": "O(N) or O(N log N)",
            "concepts_count": 2,
            "constraints_guideline": "1 <= N <= 2 * 10^5, edge cases and optimal approach required",
            "description": "Combines 2 algorithmic concepts (e.g. prefix sum + binary search, heap + greedy)."
        },
        {
            "difficulty": "Hard",
            "max_solution_lines": 70,
            "time_complexity_target": "O(N log N) or O(V + E log V)",
            "concepts_count": 3,
            "constraints_guideline": "1 <= N <= 5 * 10^5, tight limits and advanced invariants",
            "description": "Requires non-obvious mathematical insight and advanced data structures."
        },
        {
            "difficulty": "Custom",
            "max_solution_lines": 50,
            "time_complexity_target": "Custom specified",
            "concepts_count": 2,
            "constraints_guideline": "Configured per generation prompt",
            "description": "User defined difficulty parameters."
        }
    ]

    for r_data in rubrics:
        existing = db.query(DifficultyRubric).filter(DifficultyRubric.difficulty == r_data["difficulty"]).first()
        if not existing:
            db.add(DifficultyRubric(**r_data))

    # 3. Seed 3 Sample Topics with Example Questions per difficulty
    # Topic 1: Arrays (Easy, Medium, Hard)
    # Topic 2: Dynamic Programming (Easy, Medium, Hard)
    # Topic 3: Graphs (Easy, Medium, Hard)
    sample_questions = [
        # Arrays - Easy
        {
            "id": "q_seed_arrays_easy",
            "title": "Pair Difference Scanner",
            "topic": "Arrays",
            "subtopic": "Two Pointers",
            "difficulty": "Easy",
            "question_type": "coding",
            "story": "Given a sorted array of distinct integers A and an integer target K, determine if there exists any pair of indices (i, j) with i != j such that |A[i] - A[j]| == K. Output 1 if such a pair exists, otherwise 0.",
            "input_format": "The first line contains two integers N and K.\nThe second line contains N sorted space-separated integers.",
            "output_format": "Print 1 if a valid pair exists, otherwise 0.",
            "constraints": "2 <= N <= 10^5\n1 <= K <= 10^9\n1 <= A[i] <= 10^9",
            "sample_inputs": ["5 3\n1 4 8 10 15", "4 5\n1 2 3 4"],
            "sample_outputs": ["1", "0"],
            "explanation": "In sample 1, |4 - 1| = 3. In sample 2, no pair has difference 5.",
            "tags": ["arrays", "two-pointers"],
            "time_limit": 2.0,
            "memory_limit": 256,
            "reference_solution": {
                "python": (
                    "import sys\n\n"
                    "def solve():\n"
                    "    lines = sys.stdin.read().split()\n"
                    "    if not lines: return\n"
                    "    n = int(lines[0])\n"
                    "    k = int(lines[1])\n"
                    "    arr = [int(x) for x in lines[2:2+n]]\n"
                    "    i, j = 0, 1\n"
                    "    while i < n and j < n:\n"
                    "        if i != j and arr[j] - arr[i] == k:\n"
                    "            print(1)\n"
                    "            return\n"
                    "        elif arr[j] - arr[i] < k:\n"
                    "            j += 1\n"
                    "        else:\n"
                    "            i += 1\n"
                    "    print(0)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                )
            },
            "brute_force_solution": (
                "import sys\n\n"
                "def solve():\n"
                "    lines = sys.stdin.read().split()\n"
                "    if not lines: return\n"
                "    n, k = int(lines[0]), int(lines[1])\n"
                "    arr = [int(x) for x in lines[2:2+n]]\n"
                "    for i in range(n):\n"
                "        for j in range(i+1, n):\n"
                "            if abs(arr[i] - arr[j]) == k:\n"
                "                print(1)\n"
                "                return\n"
                "    print(0)\n\n"
                "if __name__ == '__main__':\n"
                "    solve()\n"
            ),
            "editorial": "Use two pointers since array is sorted, scanning in O(N) time and O(1) space.",
            "status": QuestionStatus.APPROVED.value,
            "critic_score": 9.2,
            "test_cases": [
                {"input": "5 3\n1 4 8 10 15", "output": "1", "is_sample": True, "score": 0.0},
                {"input": "4 5\n1 2 3 4", "output": "0", "is_sample": True, "score": 0.0},
                {"input": "2 0\n5 5", "output": "0", "is_sample": False, "score": 5.0},
                {"input": "6 7\n1 3 5 8 12 15", "output": "1", "is_sample": False, "score": 10.0}
            ]
        },
        # Arrays - Medium
        {
            "id": "q_seed_arrays_medium",
            "title": "Subarray Sum Modulo Partition",
            "topic": "Arrays",
            "subtopic": "Prefix Sums & HashMaps",
            "difficulty": "Medium",
            "question_type": "coding",
            "story": "Given an array of integers A and a modulo integer M, find the length of the longest contiguous subarray whose sum is divisible by M.",
            "input_format": "First line contains two integers N and M.\nSecond line contains N integers.",
            "output_format": "Output a single integer representing the maximum subarray length.",
            "constraints": "1 <= N <= 2 * 10^5\n1 <= M <= 10^5\n-10^9 <= A[i] <= 10^9",
            "sample_inputs": ["6 5\n2 7 6 1 4 5"],
            "sample_outputs": ["4"],
            "explanation": "Subarray [7, 6, 1, 4] sums to 18? Wait: [7,6,1,1] or [7, 6, 1, 4] = 18. [2, 7, 6] = 15 which is length 3. [7, 6, 1, 1] etc.",
            "tags": ["arrays", "prefix-sums", "hashmap"],
            "time_limit": 2.0,
            "memory_limit": 256,
            "reference_solution": {
                "python": (
                    "import sys\n\n"
                    "def solve():\n"
                    "    lines = sys.stdin.read().split()\n"
                    "    if not lines: return\n"
                    "    n, m = int(lines[0]), int(lines[1])\n"
                    "    arr = [int(x) for x in lines[2:2+n]]\n"
                    "    seen = {0: -1}\n"
                    "    curr_sum = 0\n"
                    "    max_len = 0\n"
                    "    for i, x in enumerate(arr):\n"
                    "        curr_sum += x\n"
                    "        rem = curr_sum % m\n"
                    "        if rem in seen:\n"
                    "            max_len = max(max_len, i - seen[rem])\n"
                    "        else:\n"
                    "            seen[rem] = i\n"
                    "    print(max_len)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                )
            },
            "editorial": "Store the earliest seen remainder modulo M in a hash map. When the same remainder appears at index i, the subarray from seen[rem]+1 to i has sum divisible by M. Runs in O(N).",
            "status": QuestionStatus.APPROVED.value,
            "critic_score": 8.9,
            "test_cases": [
                {"input": "6 5\n2 7 6 1 4 5", "output": "5", "is_sample": True, "score": 0.0},
                {"input": "3 3\n1 2 3", "output": "3", "is_sample": False, "score": 5.0}
            ]
        },
        # DP - Medium
        {
            "id": "q_seed_dp_medium",
            "title": "Monolith Energy Charge",
            "topic": "Dynamic Programming",
            "subtopic": "Linear DP",
            "difficulty": "Medium",
            "question_type": "coding",
            "story": "You have N monoliths in a line. Each monolith i provides power P[i]. You cannot activate two adjacent monoliths. Find the maximum total power you can obtain.",
            "input_format": "The first line contains an integer N.\nThe second line contains N integers representing P.",
            "output_format": "Print the maximum power possible.",
            "constraints": "1 <= N <= 2 * 10^5\n0 <= P[i] <= 10^9",
            "sample_inputs": ["4\n3 2 7 10", "5\n3 2 5 10 7"],
            "sample_outputs": ["13", "15"],
            "explanation": "In sample 1, choose index 0 (3) and index 3 (10) for total 13.",
            "tags": ["dp", "house-robber"],
            "time_limit": 2.0,
            "memory_limit": 256,
            "reference_solution": {
                "python": (
                    "import sys\n\n"
                    "def solve():\n"
                    "    lines = sys.stdin.read().split()\n"
                    "    if not lines: return\n"
                    "    n = int(lines[0])\n"
                    "    arr = [int(x) for x in lines[1:1+n]]\n"
                    "    if n == 0: print(0); return\n"
                    "    if n == 1: print(arr[0]); return\n"
                    "    prev2 = 0\n"
                    "    prev1 = 0\n"
                    "    for x in arr:\n"
                    "        curr = max(prev1, prev2 + x)\n"
                    "        prev2 = prev1\n"
                    "        prev1 = curr\n"
                    "    print(prev1)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                )
            },
            "editorial": "Standard 1D dynamic programming state dp[i] = max(dp[i-1], dp[i-2] + P[i]) optimized to O(1) space and O(N) time.",
            "status": QuestionStatus.APPROVED.value,
            "critic_score": 9.0,
            "test_cases": [
                {"input": "4\n3 2 7 10", "output": "13", "is_sample": True, "score": 0.0},
                {"input": "5\n3 2 5 10 7", "output": "15", "is_sample": True, "score": 0.0}
            ]
        },
        # Graphs - Hard
        {
            "id": "q_seed_graphs_hard",
            "title": "Quantum Relay Latency",
            "topic": "Graphs",
            "subtopic": "Shortest Path & Binary Search",
            "difficulty": "Hard",
            "question_type": "coding",
            "story": "A network has N nodes and M bidirectional quantum channels. Each channel has a latency L and a bandwidth limit B. You want to travel from node 1 to node N while maintaining at least K bandwidth. Find the minimum total latency required.",
            "input_format": "The first line contains N, M, K.\nThe next M lines each contain u, v, L, B.",
            "output_format": "Print the minimum latency, or -1 if unreachable.",
            "constraints": "2 <= N <= 10^5\n1 <= M <= 2 * 10^5\n1 <= K <= 10^9\n1 <= L, B <= 10^9",
            "sample_inputs": ["3 3 5\n1 2 4 10\n2 3 6 8\n1 3 15 2"],
            "sample_outputs": ["10"],
            "explanation": "Path 1 -> 2 -> 3 has latency 4 + 6 = 10 and min bandwidth min(10, 8) = 8 >= 5. Direct channel 1 -> 3 has bandwidth 2 < 5.",
            "tags": ["graphs", "dijkstra", "shortest-path"],
            "time_limit": 2.0,
            "memory_limit": 256,
            "reference_solution": {
                "python": (
                    "import sys, heapq\n\n"
                    "def solve():\n"
                    "    lines = sys.stdin.read().split()\n"
                    "    if not lines: return\n"
                    "    n, m, k = int(lines[0]), int(lines[1]), int(lines[2])\n"
                    "    adj = [[] for _ in range(n + 1)]\n"
                    "    idx = 3\n"
                    "    for _ in range(m):\n"
                    "        u, v, l, b = int(lines[idx]), int(lines[idx+1]), int(lines[idx+2]), int(lines[idx+3])\n"
                    "        idx += 4\n"
                    "        if b >= k:\n"
                    "            adj[u].append((v, l))\n"
                    "            adj[v].append((u, l))\n"
                    "    dist = [float('inf')] * (n + 1)\n"
                    "    dist[1] = 0\n"
                    "    pq = [(0, 1)]\n"
                    "    while pq:\n"
                    "        d, u = heapq.heappop(pq)\n"
                    "        if d > dist[u]: continue\n"
                    "        if u == n: print(d); return\n"
                    "        for v, w in adj[u]:\n"
                    "            if dist[u] + w < dist[v]:\n"
                    "                dist[v] = dist[u] + w\n"
                    "                heapq.heappush(pq, (dist[v], v))\n"
                    "    print(-1)\n\n"
                    "if __name__ == '__main__':\n"
                    "    solve()\n"
                )
            },
            "editorial": "Filter out channels where B < K since they cannot support the required bandwidth. Run Dijkstra on the filtered graph in O((V + E) log V).",
            "status": QuestionStatus.APPROVED.value,
            "critic_score": 9.3,
            "test_cases": [
                {"input": "3 3 5\n1 2 4 10\n2 3 6 8\n1 3 15 2", "output": "10", "is_sample": True, "score": 0.0},
                {"input": "2 1 10\n1 2 5 2", "output": "-1", "is_sample": False, "score": 5.0}
            ]
        }
    ]

    for q_data in sample_questions:
        existing = db.query(Question).filter(Question.id == q_data["id"]).first()
        if not existing:
            test_cases = q_data.pop("test_cases", [])
            q_model = Question(**q_data)
            db.add(q_model)
            db.flush()
            for idx, tc in enumerate(test_cases):
                db.add(TestCase(
                    question_id=q_model.id,
                    input_data=tc["input"],
                    output_data=tc["output"],
                    is_sample=tc.get("is_sample", False),
                    is_hidden=not tc.get("is_sample", False),
                    score=tc.get("score", 5.0)
                ))

    db.commit()
    logger.info("Database seeding completed successfully.")

if __name__ == "__main__":
    from backend.app.database import engine, Base, SessionLocal
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    seed_initial_data(db)
    db.close()
    print("Seed data successfully applied!")
