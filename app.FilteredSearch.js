'use strict'
const ssc = require("./ssc-api.js")
ssc.config = require("./config.json")

// Performs a filtered search (javascript filtering AFTER rest call is complete)
async function filteredSearch() {
  let a = (await ssc.scansettings.getByName("Hello Settings 2"))
  console.log(JSON.stringify(a))
}
filteredSearch();
