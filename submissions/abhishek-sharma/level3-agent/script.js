function handleInput() {
  let input = document.getElementById("input").value.toLowerCase();
  let output = "";

  if (input.includes("+") || input.includes("-") || input.includes("*") || input.includes("/")) {
    try {
      output = "Answer: " + eval(input);
    } catch {
      output = "Invalid calculation";
    }
  }

  else if (input.includes("time")) {
    let time = new Date().toLocaleTimeString();
    output = "Current time: " + time;
  }

  else if (input.includes("study")) {
    output = "Tip: Study in 25 min sessions and take breaks.";
  }

  else if (input.includes("motivation")) {
    output = "Keep going! You are doing great 🚀";
  }

  else {
    output = "I am your AI agent. Ask me about study, time, or calculations.";
  }

  document.getElementById("output").innerText = output;
}