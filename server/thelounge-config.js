"use strict";

module.exports = {
  // Public host name
  public: false,
  host: undefined,

  // Web server port
  port: 9000,

  // Bind to all interfaces
  bind: undefined,

  // Reverse proxy support
  reverseProxy: false,

  // Theme
  theme: "default",

  // Default IRC network configuration
  // This will be pre-filled for new users
  defaults: {
    name: "AntiRC Private",
    host: "ircd",
    port: 6667,
    password: "",
    tls: false,
    rejectUnauthorized: false,
    nick: "thelounge-user",
    username: "thelounge",
    realname: "The Lounge User",
    join: "#sysadmin",
    leaveMessage: "The Lounge - https://thelounge.chat",
    commands: [],
  },

  // Lock network configuration (users cannot change)
  lockNetwork: false,

  // Message display settings
  messageStorage: [
    "sqlite",
    "text",
  ],
  useHexIp: false,

  // WebIRC support (if using webirc on IRC server)
  webirc: null,

  // Identd server
  identd: {
    enable: false,
    port: 113,
  },

  // File upload
  fileUpload: {
    enable: false,
    maxFileSize: 10240,
    baseUrl: null,
  },

  // Storage policy for SQLite
  storagePolicy: {
    enabled: false,
    maxAgeDays: 7,
    deletionPolicy: "statusOnly",
  },

  // Debug
  debug: {
    ircFramework: false,
    raw: false,
  },
};
