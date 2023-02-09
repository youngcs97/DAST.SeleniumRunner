'use strict'
const { spawn } = require("child_process");
const ssc = require("./ssc-api.js")

// Primary settings
ssc.config = require("./config.json")
const name = "Example Scan"
const settings = "#FindMe"

// Fetches the CICD Token using the "Settings" name - calls "startfast()" when complete
async function main() {
  //*/
  let cicd = (await ssc.scansettings.getByText(settings)).items[0].cicdToken;
  console.log(`Captured CICD token = "${cicd}"`)
  startfast(cicd, "8156")
  startfast(cicd, "8157")
  //*/
}

// Starts the Fast Proxy with the CICD token - calls "selenium()" when complete
async function startfast(cicd, port) {
  console.log(`Starting Fast with CICD token = "${cicd}" on port ${port}`)
  const x = spawn("fast.exe", [
    "-CIToken",ssc.config.token,
    "-CICDToken",cicd,
    "-u","http://localhost:64814/api","-p", port,"-n", `${name} port ${port}`
  ])
  x.on('exit', (code, signal) => { console.log(`Fast start exited: code ${code}`); });
  x.stdout.on('data', (data) => {
    if (data.includes("Listening")) selenium(port);
    console.log(`${data}`);
  });
}

// Runs the Selenium script - calls "stopfast()" when complete
async function selenium(port) {
  console.log(`Starting selenium-side-runner proxying on ${port}`)
  const r = "selenium-side-runner";
  //const s = `--proxy-type=pac --proxy-options="http://cyoung.us/proxy-pac.js" "ZeroBank.side"`
  const s = `--proxy-type=manual --proxy-options="http=localhost:${port} bypass=[https://*.net]" "ZeroBank.side"`
  const x = spawn(`${r} ${s}`, {shell: true})
  x.stdout.on('data', (data) => { console.log(`${data}`); });
  x.on('exit', (code, signal) => {
    console.log(`${r} exited: code ${code}`);
    stopfast(port);
  });
}

// Stops the Fast Proxy
async function stopfast(port) {
  console.log(`Stopping Fast port ${port}`)
  const x = spawn("fast.exe", ["-p", port, "-s"])
  x.on('exit', (code, signal) => { console.log(`Fast stop exited: code ${code}`); });
}

main();
