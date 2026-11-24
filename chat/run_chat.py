import logging
import sys

from chat.assistant import answer_question

# Hide the "HTTP Request: ..." lines, so only the answer is printed.
logging.getLogger("httpx").setLevel(logging.WARNING)


def show_answer(result):
    print()
    print(result["answer"])

    if result["tools_used"]:
        print()
        print("Looked at: " + ", ".join(result["tools_used"]))

    if result["sources"]:
        print("Documents found: " + ", ".join(result["sources"]))

    print()


def main():
    # One question from the command line: python -m chat.run_chat "your question"
    if len(sys.argv) > 1:
        question = " ".join(sys.argv[1:])
        show_answer(answer_question(question))
        return

    # No question given: an interactive chat. An empty line ends it.
    print("Ask a question. Press Enter on an empty line to stop.")
    history = []

    while True:
        question = input("You: ").strip()

        if question == "":
            break

        result = answer_question(question, history)
        show_answer(result)

        history.append({"role": "user", "content": question})
        history.append({"role": "assistant", "content": result["answer"]})


if __name__ == "__main__":
    main()
