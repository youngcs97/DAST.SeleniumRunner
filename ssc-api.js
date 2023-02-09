'use strict';

/**
 * $: Shortnand variable for common functionality.
 */
const $ = {
    //$.${0,1,2} will be used to encapsulate logging. 0=error, 1=warning, 2=informational
    /**
     * Error message handler
     * @param {*} message 
     */
    $0: function(message) { console.error(message.substring(0, 5000)) }, 
    /**
     * Warning message handler
     * @param {*} message 
     */
    $1: function(message) { console.error(message.substring(0, 5000)) }, 
    /**
     * Informational message handler
     * @param {*} message 
     */
    $2: function(message) { if ($.config.debug) console.log(message) },


    //set defaults
    /**
     * Configuration items
     * @property {boolean} debug Whether to print debug messages to the console
     * @property {string} url Endpoint URL
     * @property {string} token Authentication token
     * @property {string} proxy Proxy setting
     */
    config: {   
        /** Whether to print debug messages to the console */
        debug: true,     
        /** Endpoint URL */ 
        url: "http://127.0.0.1:64814/api/v2",
        /** Authentication token */
        token: "token",
        /** Proxy */
        proxy: "" //"http://127.0.0.1:8888"
    },


    //request method wraps request module into a Promise
    _request: null,
    /**
     * Wraps request module into a Promise
     * @param {any} options request.options
     * @param {string} label label used for identification in messages
     * @param {any} data form-data
     * @param {boolean} parse call JSON.parse(.body) upon resolve
     * @returns {Promise<any>} Promise with the results of the http request
     */
    request: function (options, label, data = null, parse = false) {
        if (this._request == null) {        //lazy init
            this._request = require("request");
            if ($.config.proxy.length > 0) this.agent = new require('https-proxy-agent')($.config.proxy);
        }
        if ($.config.proxy.length > 0) {
            options.agent = this.agent;
            options.rejectUnauthorized = false;
        }
        options.rejectUnauthorized = false
        options.requestCert = true
        
        return new Promise((resolve, reject) => {
            var n = label;
            var r = this._request(options, (error, response, body) => {
                if (error) {
                    $.$0(n + " " +error);
                    reject(error);
                }
                var s = response.statusCode;
                if ((s >= 200)&&(s <= 299)) {     
                    $.$2(`${n}.statusCode: ${s}`);
                    resolve(parse ? JSON.parse(response.body) : response);
                } else {
                    $.$1(`${n}.statusCode = ${s}`);
                    $.$1(`${n}.body = ${JSON.stringify(response)}`);
                    reject(response);
                }
            });
            $.$2(`${n} requested.`);
            if (data!=null) {       //used to push form-data if necessary
                data.pipe(r);
                $.$2(`${n} piped.`);
            }
        });
    }
}
module.exports = {
    /**
     * Configuration items
     * @property {boolean} debug Whether to print debug messages to the console
     * @property {string} url Endpoint URL
     * @property {string} token Authentication token
     * @property {string} proxy Proxy setting
     */
    get config() {
        return $.config;
    },
    set config(value) {
        if (typeof value !== "undefined") {
            Object.keys(value).forEach(function(key,index) {
                if (typeof $.config[key] !== "undefined") $.config[key]=value[key];
            });
        }
    }
}


/**
 * Module for Scan Settings
 */
const scansettings = {
    /**
     * Gets all Scan Settings.
     * @param {Array<string>} token Token
     */
    getAll: async function (token = $.config.token) {
        return this.getByText(null, token)
    },
    /**
     * Gets all Scan Settings containing text.
     * @param {string} text Hashtag to search
     * @param {Array<string>} token Token
     */
    getByText: async function (text = null, token = $.config.token) {
        var n = "scan-settings";
        var q = ((text||'').trim().length > 0) ? "?searchText="+encodeURIComponent(text) : ""
        $.$2(n + '.request()');
        var o = {
            method: 'GET',
            url: `${$.config.url}/application-version-scan-settings/scan-settings-summary-list${q}`,
            headers: { "Content-Type": "application/json", "Authorization": `FortifyToken ${token}`}
        }
        return $.request(o, n, null, true);
    },
    /**
     * Gets all Scan Settings by Name.
     * @param {string} name Name to search
     * @param {Array<string>} token Token
     */
    getByName: async function (name = null, token = $.config.token) {
        var r = this.getByText(name, token)
        return new Promise((resolve, reject) => {
            Promise.all([r]).then(function(s){ 
                var f = s[0]
                if (((name||'').trim().length > 0) && (f.items!=null)) {
                    f.items = f.items.filter(v => { return ((v.name||'').toLowerCase()==name.toLowerCase()) });
                    f.filteredItems = f.items.length
                }
                resolve(f);
            }).catch((error)=>{ $.$0(error); reject(error); })
        });
    }
}
module.exports.scansettings = scansettings

