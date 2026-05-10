function generatePlan() {
    const city = document.getElementById("destination").value.toLowerCase();
    const days = parseInt(document.getElementById("days").value);
  
    const plans = {
      rishikesh: [
        "Visit Laxman Jhula 🌉",
        "River rafting 🚣",
        "Yoga & Ganga Aarti 🧘",
        "Waterfall visit 💧",
        "Cafe hopping ☕"
      ],
      manali: [
        "Mall Road visit 🛍️",
        "Solang Valley 🏔️",
        "Rohtang Pass ❄️",
        "Cafe hopping ☕",
        "Local sightseeing 🚗"
      ],
      goa: [
        "Beach day 🏖️",
        "Water sports 🚤",
        "Night party 🎉",
        "Fort Aguada 🏰",
        "Relax at beach 🌅"
      ]
    };
  
    const weather = {
      rishikesh: "Warm & pleasant 🌤️",
      manali: "Cold & snowy ❄️",
      goa: "Hot & humid 🌞"
    };
  
    const defaultPlan = [
      "Explore local area 🏙️",
      "Visit tourist spots 📍",
      "Try local food 🍲",
      "Shopping 🛍️",
      "Relaxation 😌"
    ];
  
    let cityPlan = plans[city] || defaultPlan;
  
    let output = `<h2>Trip Plan for ${city}</h2>`;
  
    for (let i = 0; i < days; i++) {
      let activity = cityPlan[i % cityPlan.length];
      output += `
        <div class="day-card">
          <h3>Day ${i + 1}</h3>
          <p>${activity}</p>
        </div>
      `;
    }
  
    let budget = days * 2000;
  
    output += `
      <h3>💰 Estimated Budget: ₹${budget}</h3>
      <h3>🌤️ Weather: ${weather[city] || "Moderate"}</h3>
    `;
  
    document.getElementById("output").innerHTML = output;
  }