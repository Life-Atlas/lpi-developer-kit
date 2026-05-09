const { spawn } = require("child_process");

const process = spawn("node", ["dist/src/index.js"]);

process.stdout.on("data", (data) => {
  console.log(data.toString());
});

process.stderr.on("data", (data) => {
  console.error(data.toString());
});