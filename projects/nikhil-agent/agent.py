# AI Fraud Detection Agent with Error Handling and Explanation

def detect_fraud(amount, location, frequency):
    """
    Detect fraud based on transaction patterns.
    Returns status and explanation.
    """

    if amount > 10000 and location.lower() != "home":
        return "⚠️ High Risk", "Large transaction from unusual location"

    elif frequency > 5:
        return "⚠️ Suspicious", "Too many transactions in a short time"

    else:
        return "✅ Safe", "Normal transaction behavior"


def run_agent():
    """
    Main function to run the fraud detection agent.
    Handles user input and errors gracefully.
    """

    print("=== AI Fraud Detection Agent ===")

    try:
        # User inputs
        amount = float(input("Enter transaction amount: "))
        location = input("Enter location: ").strip()
        frequency = int(input("Transactions today: "))

        # Input validation
        if location == "":
            print("❌ Error: Location cannot be empty.")
            return

        if amount < 0 or frequency < 0:
            print("❌ Error: Values cannot be negative.")
            return

        # Fraud detection
        status, reason = detect_fraud(amount, location, frequency)

        # Output
        print("\n🔍 Result:")
        print("Status:", status)
        print("Reason:", reason)

    except ValueError:
        print("❌ Invalid input. Please enter correct numeric values.")

    except Exception:
        print("⚠️ Unexpected error occurred. Please try again.")


if __name__ == "__main__":
    run_agent()