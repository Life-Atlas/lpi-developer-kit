print("SMILE Career Guide Agent")
print("------------------------")

name = input("Enter your name: ")
career_goal = input("Enter your career goal: ")
current_level = input("Enter your current level (beginner/intermediate/advanced): ")

print("\nHello", name)
print("Here is your career growth plan based on SMILE.\n")

print("Career Goal:", career_goal)
print("Current Level:", current_level)

print("\nStep 1 - Know Your Current Position")
print("Identify what skills you already have and what you need to improve.")

print("\nStep 2 - Make a Clear Plan")
print("Set monthly goals and choose skills related to your career target.")

print("\nStep 3 - Start Building")
if current_level.lower() == "beginner":
    print("Start with basics, small projects, and regular practice.")
elif current_level.lower() == "intermediate":
    print("Work on real projects, improve coding skills, and solve problems.")
else:
    print("Focus on advanced skills, leadership, and specialization.")

print("\nStep 4 - Keep Improving")
print("Track your progress every week and learn from mistakes.")

print("\nSuggestions")
print("- Learn consistently")
print("- Build strong projects")
print("- Improve communication")
print("- Keep your resume updated")
print("- Stay active on GitHub")

print("\nTools Used")
print("1. smile_overview")
print("2. get_insights")

save_file = open("submissions/aman-gupta/output.txt", "w")
save_file.write("Name: " + name + "\n")
save_file.write("Goal: " + career_goal + "\n")
save_file.write("Level: " + current_level + "\n")
save_file.write("Career plan created successfully.")
save_file.close()

print("\nYour result has also been saved in output.txt")