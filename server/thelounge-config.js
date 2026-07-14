"use strict";

module.exports = {
  // Public host name
  public: true,
  host: undefined,

  // Web server port
  port: 9000,

  // Bind to all interfaces
  bind: undefined,

  // Reverse proxy support
  reverseProxy: false,

  // Theme
  theme: "themes/default.css",

  // Default preferences for new users
  defaults: {
    name: "AntiRC",
    nick: "thelounge-user",
    username: "thelounge",
    realname: "The Lounge User",
    join: "#sysadmin",
    leaveMessage: "The Lounge - https://thelounge.chat",
  },

  // Default IRC network configuration
  // This will be pre-filled for new users
  defaultsNetwork: {
    name: "AntiRC Private",
    host: "ircd",
    port: 6667,
    password: "",
    tls: false,
    rejectUnauthorized: false,
    nick: "thelounge-user",
    username: "thelounge",
    realname: "The Lounge User",
    commands: [],
    channels: "#sysadmin",
  },

  // Lock network configuration (users cannot change)
  lockNetwork: false,

  // Message display settings
  messageStorage: [
    "text",
    "sqlite",
  ],
  useHexIp: false,

  // WebIRC support (if using webirc on IRC server)
  webirc: {
    // coincidences: {
    //   "ircd": "webirc_password",
    // },
  },

  // Identd server
  identd: {
    enable: false,
    port: 113,
  },

  // Authentication
  // Use The Lounge's built-in authentication
  // Users must be added via: thelounge add <username>
  authentication: {
    method: "native",
    timeout: 30000,
  },

  // File upload
  fileUpload: {
    enable: false,
    maxFileSize: 10485760,
  },

  // Push notifications
  pushNotifications: {
    enabled: false,
  },

  // Logging
  logs: {
    format: "simple",
    maxLines: 10000,
    writeInterval: 100,
  },

  // Debug
  debug: {
    ircFramework: false,
    raw: false,
  },

  // SQLite message storage
  sqlite: {
    enabled: true,
    path: "./sqlite",
    logs: {
      enabled: true,
      deleteInterval: 7 * 24 * 60 * 60 * 1000, // 7 days
    },
  },
};
