from scripts.db import Database

MEMORY_QUESTIONS: dict[str, list[str]] = {
    "memory": [
        "你童年最深刻的记忆是什么？",
        "你人生中最骄傲的一件事是什么？",
        "你经历过最困难的时期是什么？你是怎么度过的？",
        "有没有一个人对你影响最深？他/她是谁，怎么影响了你？",
        "你最难忘的一次旅行或经历是什么？",
        "你小时候的梦想是什么？",
        "有没有一件你后悔过的事？",
        "你人生中最快乐的时刻是什么？",
        "你的家庭对你的成长有什么影响？",
        "如果可以重来，你会改变什么？",
    ],
    "habits": [
        "你通常怎么做决定？靠直觉还是仔细分析？",
        "你是早起的人还是夜猫子？",
        "遇到压力时你通常怎么处理？",
        "你喜欢独处还是和别人在一起？",
        "你有什么坚持多年的习惯？",
        "你通常怎么学习新东西？",
        "你对金钱的态度是什么？",
        "你怎么看待规则？你会打破规则吗？",
        "你在工作或学习中最看重什么？",
        "你如何面对失败？",
    ],
    "relationships": [
        "你如何看待友情？什么样的人是你的真朋友？",
        "你和家人的关系怎么样？",
        "你在感情中最看重什么？",
        "你有没有很难维持的人际关系？为什么？",
        "当朋友需要帮助时，你通常怎么做？",
        "你有没有因为某件事失去过重要的朋友？",
        "你怎么看待背叛？",
        "你觉得自己是一个好的倾听者吗？",
        "你怎么处理和别人的矛盾？",
        "你最珍视的人际关系是什么？",
    ],
    "style": [
        "你平时说话偏正式还是随意？",
        "你喜欢用幽默化解尴尬吗？",
        "你表达不同意见时通常怎么做？",
        "你倾向于直接说还是委婉地表达？",
        "当你生气时，你通常怎么表达？",
        "你喜欢长篇大论还是简短直接？",
        "你经常用口头禅吗？有哪些？",
        "你喜欢聊什么话题？",
        "有什么话题是你完全不感兴趣的？",
        "你希望别人怎么记住你？",
    ],
}

SCENARIO_QUESTIONS: list[str] = [
    "朋友请你帮忙说一个善意的谎言来保护他，你会怎么做？",
    "你发现同事在走捷径但没有违法，你会举报吗？",
    "有人要你做一件你觉得不道德但不违法的事，你会做吗？",
    "当你的利益和朋友的利益冲突时，你通常怎么选择？",
    "如果你知道一个秘密说出来会伤害别人，你会说吗？",
]

RED_LINE_QUESTIONS: list[str] = [
    "有什么事是你无论如何都不会做的？",
    "什么行为会让你立刻对一个人失去好感？",
    "有没有某些原则是你绝对不会妥协的？",
]

VALUES_LIST: list[str] = [
    "诚实", "家庭", "自由", "忠诚", "公平",
    "事业", "金钱", "创造力", "责任", "善良",
    "健康", "友情", "知识", "信仰", "勇气"
]


def run_questionnaire(persona_id: int, db: Database) -> dict:
    """
    Interactive CLI questionnaire. Returns values_profile dict.
    Saves all answers to db.
    """
    print("\n=== 开始填写问卷 ===\n")

    # Part 1: Memory questions
    for dimension, questions in MEMORY_QUESTIONS.items():
        print(f"\n--- {dimension.upper()} 维度 ---\n")
        for q in questions:
            print(f"问题：{q}")
            answer = input("你的回答：").strip()
            if answer:
                db.save_answer(persona_id, dimension, q, answer)

    # Part 2: Emotion baseline
    print("\n--- 情绪基线 ---\n")
    print("以下问题帮助建立你的情绪基线（0-100分）\n")

    while True:
        raw_ie = input("你平时整体情绪状态如何？（0=很差，100=很好）: ").strip()
        if raw_ie.lstrip("-").isdigit():
            base_emotion = max(0, min(100, int(raw_ie)))
            break
        print("请输入 0 到 100 之间的数字")

    while True:
        raw_type = input("你更容易悲伤(1) 还是愤怒(2)？ [1/2]: ").strip()
        if raw_type in ("1", "2"):
            break
        print("请输入 1 或 2")
    emotion_type = "sad" if raw_type == "1" else "angry"
    base_sadness = 65 if emotion_type == "sad" else 80
    base_anger = 65 if emotion_type == "angry" else 80

    for q in ["什么情况下你会感到悲伤？",
              "什么情况下你会感到愤怒？",
              "你恢复心情通常需要多久？（很快/一般/很慢）"]:
        print(f"\n{q}")
        ans = input("你的回答：").strip()
        if ans:
            db.save_answer(persona_id, "emotion_baseline", q, ans)

    # Part 3: Values ranking
    print("\n--- 价值观排序 ---\n")
    print("以下是一些价值观，请选出对你最重要的5个（输入编号，用逗号分隔）：\n")
    for i, v in enumerate(VALUES_LIST, 1):
        print(f"  {i}. {v}")
    raw = input("\n你的选择（例如：1,3,5,7,9）: ").strip()
    indices = [int(x.strip()) - 1 for x in raw.split(",") if x.strip().isdigit()]
    core_values = [VALUES_LIST[i] for i in indices if 0 <= i < len(VALUES_LIST)][:5]
    if len(core_values) < 5:
        print(f"注意：你只选择了 {len(core_values)} 个价值观（建议5个）")

    # Part 4: Scenario questions
    print("\n--- 情景题 ---\n")
    scenario_answers: dict[str, str] = {}
    for q in SCENARIO_QUESTIONS:
        print(f"\n{q}")
        ans = input("你的回答：").strip()
        if ans:
            db.save_answer(persona_id, "scenarios", q, ans)
            scenario_answers[q] = ans

    # Part 5: Red lines
    print("\n--- 红线 ---\n")
    red_lines: list[str] = []
    for q in RED_LINE_QUESTIONS:
        print(f"\n{q}")
        ans = input("你的回答：").strip()
        if ans:
            db.save_answer(persona_id, "red_lines", q, ans)
            red_lines.append(ans)

    return {
        "base_emotion": base_emotion,
        "base_sadness": base_sadness,
        "base_anger": base_anger,
        "core_values": core_values,
        "red_lines": red_lines,
        "scenarios": scenario_answers,
    }
