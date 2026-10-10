window.LaunchpadInterview = (() => {
  const questions = [
    { id: "fundamentals-complexity", category: "Technical", skill: "dsa", topic: "Programming fundamentals", difficulty: "Beginner", roles: ["Software Developer", "Web Developer", "AI Engineer"], prompt: "A loop visits each item in an array once. Explain its time complexity and how you would reason about it.", keyPoints: [["n iterations", "each item"], ["linear", "O(n)"], ["input size", "grows"]], outline: "State that the loop performs one unit of work per item, so its running time grows linearly with input size: O(n). Mention the input variable n and any assumptions." },
    { id: "fundamentals-oop", category: "Technical", skill: "dsa", topic: "Object-oriented programming", difficulty: "Intermediate", roles: ["Software Developer", "Web Developer"], prompt: "Explain encapsulation and give an example of how it helps maintain a class invariant.", keyPoints: [["encapsulation", "hide"], ["private", "access"], ["invariant", "validation"]], outline: "Define encapsulation as controlling access to state through a public interface. Give a concrete example where a method validates updates so an invariant remains true." },
    { id: "fundamentals-memory", category: "Technical", skill: "dsa", topic: "Programming fundamentals", difficulty: "Advanced", roles: ["Software Developer", "AI Engineer"], prompt: "When diagnosing high memory use in a service, what measurements and hypotheses would you check before changing code?", keyPoints: [["profile", "heap", "memory"], ["baseline", "measure"], ["leak", "retained", "allocation"], ["reproduce", "load"]], outline: "Establish a baseline, inspect heap/allocation profiles under representative load, identify retained objects or excessive allocations, reproduce the issue, and verify the change with the same measurement." },
    { id: "fundamentals-sql", category: "Technical", skill: "web", topic: "Database fundamentals and SQL", difficulty: "Beginner", roles: ["Software Developer", "Data Analyst", "Web Developer"], prompt: "What is the purpose of a primary key, and why should it be stable and unique?", keyPoints: [["unique", "uniquely"], ["identify", "identifier"], ["null", "not null"], ["foreign key", "reference"]], outline: "Explain that a primary key identifies exactly one row, must be unique and non-null, and is referenced by related records. A stable key avoids breaking relationships when descriptive data changes." },
    { id: "fundamentals-ai", category: "Technical", skill: "aptitude", topic: "AI and machine-learning basics", difficulty: "Intermediate", roles: ["AI Engineer", "Data Analyst"], prompt: "Distinguish training, validation, and test data, and explain one risk of using the test set repeatedly during model tuning.", keyPoints: [["training", "fit", "learn"], ["validation", "tune", "select"], ["test", "unseen", "final"], ["leak", "overfit", "bias"]], outline: "Describe training as fitting parameters, validation as choosing configurations, and test data as a final unseen estimate. Repeated test-set tuning leaks information and makes the reported result optimistic." },
    { id: "dsa-arrays", category: "DSA", skill: "dsa", topic: "Arrays and strings", difficulty: "Beginner", roles: ["Software Developer", "Data Analyst", "AI Engineer", "Web Developer"], prompt: "How would you find the largest value in an unsorted integer array in one pass? State the complexity.", keyPoints: [["maximum", "largest"], ["scan", "iterate", "traverse"], ["O(n)", "linear"], ["O(1)", "constant space"]], outline: "Initialize the best value from the first element, scan the rest while updating it, and return it. Time is O(n); extra space is O(1)." },
    { id: "dsa-two-pointers", category: "DSA", skill: "dsa", topic: "Two pointers", difficulty: "Intermediate", roles: ["Software Developer", "AI Engineer"], prompt: "For a sorted array, explain how two pointers can determine whether a pair sums to a target in linear time.", keyPoints: [["sorted", "order"], ["left", "right", "ends"], ["sum", "target"], ["move", "O(n)", "linear"]], outline: "Start at both ends. If the sum is too small, move the left pointer right; if too large, move the right pointer left. Each pointer advances at most n times, so time is O(n)." },
    { id: "dsa-binary-search", category: "DSA", skill: "dsa", topic: "Searching and sorting", difficulty: "Beginner", roles: ["Software Developer", "Data Analyst", "AI Engineer"], prompt: "What condition does binary search require, and why does each comparison discard half of the search range?", keyPoints: [["sorted", "monotonic"], ["middle", "midpoint"], ["half", "discard"], ["O(log n)", "logarithmic"]], outline: "The search space must be sorted or monotonic. Compare the midpoint with the target, use ordering to discard one half, and repeat in O(log n) time." },
    { id: "dsa-hashmap", category: "DSA", skill: "dsa", topic: "Hash maps", difficulty: "Intermediate", roles: ["Software Developer", "Data Analyst", "AI Engineer", "Web Developer"], prompt: "How can a hash map help find whether an array contains two values that sum to a target? Discuss average complexity.", keyPoints: [["complement", "target minus"], ["hash", "set", "map"], ["lookup", "check"], ["O(n)", "linear"]], outline: "Scan once, checking whether the complement of each value has already been seen; then store the current value. Average time and space are O(n)." },
    { id: "dsa-graphs", category: "DSA", skill: "dsa", topic: "Graphs and BFS", difficulty: "Advanced", roles: ["Software Developer", "AI Engineer"], prompt: "Why does breadth-first search find a shortest path in an unweighted graph, and what must an implementation track?", keyPoints: [["level", "layers", "distance"], ["queue", "FIFO"], ["visited", "mark"], ["unweighted", "equal edge"]], outline: "BFS explores vertices in nondecreasing edge distance using a FIFO queue. Track visited vertices (and often parents/distances), marking visited when enqueued to avoid duplicate work." },
    { id: "web-html", category: "Web Development", skill: "web", topic: "Semantic HTML and accessibility", difficulty: "Beginner", roles: ["Web Developer", "Software Developer"], prompt: "Why use semantic HTML landmarks such as main, nav, and button instead of generic div elements everywhere?", keyPoints: [["meaning", "semantic"], ["accessibility", "screen reader"], ["keyboard", "native"], ["structure", "landmark"]], outline: "Semantic elements communicate purpose to browsers and assistive technology, provide useful landmarks, and offer native keyboard and interaction behavior where appropriate." },
    { id: "web-css", category: "Web Development", skill: "web", topic: "Responsive CSS", difficulty: "Beginner", roles: ["Web Developer", "Software Developer"], prompt: "How would you build a card layout that uses three columns on wide screens and one column on narrow screens?", keyPoints: [["grid", "flex"], ["media query", "breakpoint"], ["responsive", "narrow"], ["minmax", "fraction", "fr"]], outline: "Use CSS Grid with flexible columns such as repeat(3, minmax(0, 1fr)); at a chosen breakpoint change to one column. Check content overflow and keyboard order." },
    { id: "web-async", category: "Web Development", skill: "web", topic: "JavaScript asynchronous requests", difficulty: "Intermediate", roles: ["Web Developer", "Software Developer", "AI Engineer"], prompt: "When using fetch, how should an interface handle loading, HTTP errors, network errors, and successful data?", keyPoints: [["loading", "pending"], ["response.ok", "status", "HTTP"], ["catch", "network", "error"], ["success", "render", "data"]], outline: "Show loading state, check response.ok/status because HTTP errors do not necessarily reject fetch, parse and render successful data, and catch network/parsing errors with a clear retryable message." },
    { id: "web-xss", category: "Web Development", skill: "web", topic: "Web security", difficulty: "Advanced", roles: ["Web Developer", "Software Developer"], prompt: "What is cross-site scripting, and how would you reduce the risk when displaying user-submitted text?", keyPoints: [["script", "javascript", "injection"], ["escape", "encode", "textContent"], ["sanitize", "allowlist"], ["CSP", "content security"]], outline: "XSS executes attacker-controlled script in another user's browser. Prefer safe text sinks such as textContent, contextually encode output, sanitize only when rich HTML is required, and add defense-in-depth policies." },
    { id: "web-api", category: "Web Development", skill: "web", topic: "API and form validation", difficulty: "Intermediate", roles: ["Web Developer", "Software Developer", "Data Analyst"], prompt: "Why must an API validate submitted data even if the browser already validates the same form?", keyPoints: [["browser", "client", "bypass"], ["server", "API", "trust"], ["type", "range", "required"], ["authorization", "security"]], outline: "Client validation improves feedback but can be bypassed. The server must independently validate types, required fields, ranges, and authorization before trusting or storing input." },
    { id: "aptitude-percent", category: "Aptitude", skill: "aptitude", topic: "Percentages", difficulty: "Beginner", roles: ["Software Developer", "Data Analyst", "AI Engineer", "Web Developer"], prompt: "A value rises from 80 to 100. Calculate the percentage increase and explain which value is the base.", keyPoints: [["increase", "20"], ["base", "original", "80"], ["20 divided by 80", "20/80"], ["25%", "25 percent"]], outline: "The increase is 100 − 80 = 20. Divide by the original value 80 and multiply by 100: 20/80 × 100 = 25%." },
    { id: "aptitude-work", category: "Aptitude", skill: "aptitude", topic: "Time and work", difficulty: "Intermediate", roles: ["Software Developer", "Data Analyst", "AI Engineer", "Web Developer"], prompt: "One worker completes a job in 6 days and another in 3 days. How long do they take together? Show the rate calculation.", keyPoints: [["1/6", "one sixth"], ["1/3", "one third"], ["1/2", "half"], ["2 days", "two days"]], outline: "Their daily rates add: 1/6 + 1/3 = 1/2 job/day. The time for one job is the reciprocal, 2 days." },
    { id: "aptitude-probability", category: "Aptitude", skill: "aptitude", topic: "Probability", difficulty: "Beginner", roles: ["Software Developer", "Data Analyst", "AI Engineer", "Web Developer"], prompt: "A fair six-sided die is rolled. What is the probability of an even result? Explain the sample space.", keyPoints: [["six", "6 outcomes"], ["2, 4, 6", "three even"], ["3/6", "three out of six"], ["1/2", "one half"]], outline: "The sample space has six equally likely outcomes; three are even (2, 4, 6). Probability is 3/6 = 1/2." },
    { id: "aptitude-data", category: "Aptitude", skill: "aptitude", topic: "Data interpretation", difficulty: "Advanced", roles: ["Data Analyst", "AI Engineer", "Software Developer"], prompt: "A metric increases by 10% and then decreases by 10%. Is it back at its original value? Demonstrate with a starting value of 100.", keyPoints: [["110", "100 increased"], ["99", "decrease 11"], ["not equal", "not back", "not the same"], ["different base", "multiplicative"]], outline: "Starting at 100, a 10% increase gives 110. A 10% decrease is 11 (10% of 110), leaving 99, so sequential percentage changes do not cancel." },
    { id: "aptitude-series", category: "Aptitude", skill: "aptitude", topic: "Number series", difficulty: "Beginner", roles: ["Software Developer", "Data Analyst", "AI Engineer", "Web Developer"], prompt: "Find the next number in 2, 6, 12, 20, ... and explain the pattern.", keyPoints: [["4, 6, 8", "differences"], ["10", "next difference"], ["30", "next number"], ["increasing by 2", "pattern"]], outline: "The successive differences are 4, 6, and 8, increasing by 2. The next difference is 10, so the next term is 20 + 10 = 30." },
    { id: "aptitude-logic", category: "Aptitude", skill: "aptitude", topic: "Logical reasoning", difficulty: "Intermediate", roles: ["Software Developer", "Data Analyst", "AI Engineer", "Web Developer"], prompt: "All registered candidates received an email. Mira is registered. What conclusion follows, and what cannot be inferred?", keyPoints: [["Mira", "registered"], ["received an email", "email"], ["does not follow", "cannot infer"], ["passed", "opened"]], outline: "The premise entails that Mira received an email. It does not establish that she passed an exam or opened the message." },
    { id: "hr-star", category: "HR/Behavioral", skill: "communication", topic: "Behavioral interview · STAR", difficulty: "Beginner", roles: ["Software Developer", "Data Analyst", "AI Engineer", "Web Developer"], prompt: "Tell me about a challenging goal you completed. Structure your answer with Situation, Task, Action, and Result.", keyPoints: [["situation", "context"], ["task", "responsibility", "goal"], ["action", "specific", "I"], ["result", "outcome", "learned"]], outline: "Use STAR: briefly set the context, state your responsibility, describe your own specific actions, and finish with an honest result or lesson. Do not invent outcomes." },
    { id: "hr-conflict", category: "HR/Behavioral", skill: "communication", topic: "Teamwork and conflict", difficulty: "Intermediate", roles: ["Software Developer", "Data Analyst", "AI Engineer", "Web Developer"], prompt: "Describe how you would handle a technical disagreement with a teammate when a delivery deadline is close.", keyPoints: [["listen", "understand"], ["evidence", "trade-off", "criteria"], ["communicate", "discuss"], ["decision", "document", "deadline"]], outline: "A strong response shows listening, comparing options against shared evidence and constraints, communicating trade-offs, agreeing on a decision, and recording follow-up without personalizing disagreement." },
    { id: "hr-feedback", category: "HR/Behavioral", skill: "communication", topic: "Receiving feedback", difficulty: "Advanced", roles: ["Software Developer", "Data Analyst", "AI Engineer", "Web Developer"], prompt: "How do you respond when a reviewer identifies a serious issue in work you are proud of?", keyPoints: [["listen", "clarify"], ["ownership", "acknowledge"], ["fix", "action", "test"], ["learn", "follow up"]], outline: "Acknowledge the feedback, ask clarifying questions, take ownership, agree a fix and verification plan, then share what you learned. Use a genuine example if you have one." }
  ];

  function selectQuestions({ role, category, difficulty, count, previousIds = [], random = Math.random }) {
    const normalizedRole = role === "Custom role" ? "" : role;
    const matches = questions.filter(item =>
      (category === "Mixed" || item.category === category) &&
      (difficulty === "All levels" || item.difficulty === difficulty) &&
      (!normalizedRole || item.roles.includes(normalizedRole))
    );
    const previous = new Set(previousIds);
    const unseen = matches.filter(item => !previous.has(item.id));
    const prioritized = unseen.length >= count ? unseen : [...unseen, ...matches.filter(item => previous.has(item.id))];
    return prioritized.map(item => ({ item, sort: random() })).sort((a, b) => a.sort - b.sort).slice(0, count).map(({ item }) => item);
  }

  function evaluateAnswer(question, answer) {
    const text = String(answer || "").trim();
    if (!text) return { score: 0, dimensions: { correctness: 0, relevance: 0, reasoning: 0, completeness: 0, communication: 0 }, strengths: [], missing: question.keyPoints.map(point => point[0]), outline: question.outline, nextTopic: question.topic, wordCount: 0 };
    const lower = text.toLowerCase();
    const wordCount = (lower.match(/\b[\p{L}\p{N}+#.-]+\b/gu) || []).length;
    const matched = question.keyPoints.filter(point => point.some(term => lower.includes(term.toLowerCase())));
    const correctness = Math.round(matched.length / question.keyPoints.length * 100);
    const promptWords = question.prompt.toLowerCase().match(/\b[a-z]{4,}\b/g) || [];
    const stopWords = new Set(["what", "when", "which", "would", "could", "should", "explain", "discuss", "about", "from", "this", "that", "with", "your", "does", "have", "each", "then"]);
    const anchors = [...new Set(promptWords.filter(word => !stopWords.has(word)))];
    const relevanceHits = anchors.filter(word => lower.includes(word)).length;
    const relevance = Math.min(100, Math.round(relevanceHits / Math.max(1, Math.min(5, anchors.length)) * 100));
    const reasoning = Math.min(100, (wordCount >= 50 ? 65 : wordCount >= 25 ? 45 : wordCount >= 12 ? 25 : 10) + (/\b(because|therefore|since|so|for example|for instance|first|then|which means)\b/i.test(text) ? 25 : 0) + (/\b(time|space|trade.?off|assume|measure|verify|test)\b/i.test(text) ? 10 : 0));
    const completeness = Math.min(100, Math.round(matched.length / question.keyPoints.length * 100) + (wordCount >= 35 ? 15 : 0));
    const sentences = text.split(/[.!?]+/).filter(sentence => sentence.trim()).length;
    const communication = Math.min(100, (wordCount >= 20 && wordCount <= 180 ? 65 : wordCount >= 10 && wordCount <= 240 ? 45 : 20) + (sentences >= 2 ? 20 : 0) + (/\b(I|we|for example|because|result|therefore)\b/i.test(text) ? 15 : 0));
    const dimensions = { correctness, relevance, reasoning, completeness: Math.min(100, completeness), communication };
    const score = Math.round(correctness * .45 + relevance * .2 + reasoning * .15 + completeness * .1 + communication * .1);
    const strengths = Object.entries(dimensions).filter(([, value]) => value >= 65).map(([key]) => key);
    const missing = question.keyPoints.filter(point => !matched.includes(point)).map(point => point[0]);
    return { score, dimensions, strengths, missing, outline: question.outline, nextTopic: missing.length ? question.topic : null, wordCount };
  }

  function summarizeSession(session) {
    const answered = session.questions.map((question, index) => ({ question, answer: session.answers[index] || "", evaluation: session.evaluations[index] || null })).filter(item => item.evaluation);
    const categoryScores = {};
    for (const item of answered) {
      categoryScores[item.question.category] ||= { score: 0, total: 0 };
      categoryScores[item.question.category].score += item.evaluation.score;
      categoryScores[item.question.category].total += 1;
    }
    const topicScores = {};
    for (const item of answered) {
      topicScores[item.question.topic] ||= { score: 0, total: 0 };
      topicScores[item.question.topic].score += item.evaluation.score;
      topicScores[item.question.topic].total += 1;
    }
    const score = answered.length ? Math.round(answered.reduce((sum, item) => sum + item.evaluation.score, 0) / answered.length) : 0;
    return {
      id: session.id,
      role: session.role,
      category: session.category,
      difficulty: session.difficulty,
      score,
      answered: answered.length,
      total: session.questions.length,
      durationSeconds: Math.max(0, Math.round((Date.now() - session.startedAt) / 1000)),
      completedAt: new Date().toISOString(),
      questions: answered,
      categoryScores: Object.fromEntries(Object.entries(categoryScores).map(([key, value]) => [key, Math.round(value.score / value.total)])),
      topicScores: Object.fromEntries(Object.entries(topicScores).map(([key, value]) => [key, Math.round(value.score / value.total)])),
      strengths: [...new Set(answered.flatMap(item => item.evaluation.strengths))],
      weakTopics: [...new Set(answered.filter(item => item.evaluation.score < 60).map(item => item.question.topic))],
      nextTopics: [...new Set(answered.map(item => item.evaluation.nextTopic).filter(Boolean))]
    };
  }

  function adaptiveScore({ progress, practiceAccuracy, interviewScore }) {
    const factors = [{ value: progress, weight: .5 }];
    if (Number.isFinite(practiceAccuracy)) factors.push({ value: practiceAccuracy, weight: .2 });
    if (Number.isFinite(interviewScore)) factors.push({ value: interviewScore, weight: .3 });
    const weight = factors.reduce((sum, item) => sum + item.weight, 0);
    return Math.round(factors.reduce((sum, item) => sum + item.value * item.weight, 0) / weight);
  }

  return { questions, selectQuestions, evaluateAnswer, summarizeSession, adaptiveScore };
})();
