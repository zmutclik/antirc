; AntiRC Admin Script for mIRC
; Provides rich admin interface for managing AntiRC bot fleet
; Install: Copy to mIRC Remotes (Alt+R) and press F5

; ========== CONFIGURATION ==========
alias antirc.server return irc.antirc.local
alias antirc.channel return #sysadmin
alias antirc.nick return antirc-admin

; ========== INITIALIZATION ==========
on *:START: {
  antirc.init
}

alias antirc.init {
  ; Create custom windows
  window -De @AntiRC_Status
  window -De @AntiRC_Alerts
  window -De @AntiRC_Log

  ; Set window titles
  titlebar @AntiRC_Status AntiRC Server Status Monitor
  titlebar @AntiRC_Alerts AntiRC Security Alerts
  titlebar @AntiRC_Log AntiRC Command Log

  ; Print headers
  aline -p @AntiRC_Status $str(=,80)
  aline -p @AntiRC_Status AntiRC Server Status Monitor - Started at $asctime
  aline -p @AntiRC_Status $str(=,80)
  aline -p @AntiRC_Status $chr(160)
  aline -p @AntiRC_Status Server Name $chr(9) Status $chr(9) CPU $chr(9) RAM $chr(9) Disk $chr(9) Load $chr(9) Last Seen
  aline -p @AntiRC_Status $str(-,80)

  aline -p @AntiRC_Alerts $str(=,80)
  aline -p @AntiRC_Alerts AntiRC Security Alerts - Started at $asctime
  aline -p @AntiRC_Alerts $str(=,80)

  aline -p @AntiRC_Log $str(=,80)
  aline -p @AntiRC_Log AntiRC Command Log - Started at $asctime
  aline -p @AntiRC_Log $str(=,80)

  echo -a  AntiRC Admin Interface initialized. Connect to $antirc.server and join $antirc.channel
}

; ========== CONNECTION ==========
on *:CONNECT: {
  if ($server == $antirc.server) {
    join $antirc.channel
    nick $antirc.nick
    msg $antirc.channel !status
    msg $antirc.channel !alerts
  }
}

; ========== COMMAND ALIASES ==========
alias antirc.status {
  if ($connected) {
    msg $antirc.channel !status
    aline -p @AntiRC_Log [ $+ $asctime $+ ] Sent: !status to all bots
  }
  else {
    echo -a  Not connected to IRC server
  }
}

alias antirc.disk {
  if ($connected) {
    msg $antirc.channel !disk
    aline -p @AntiRC_Log [ $+ $asctime $+ ] Sent: !disk to all bots
  }
}

alias antirc.services {
  if ($connected) {
    msg $antirc.channel !services
    aline -p @AntiRC_Log [ $+ $asctime $+ ] Sent: !services to all bots
  }
}

alias antirc.net {
  if ($connected) {
    msg $antirc.channel !net
    aline -p @AntiRC_Log [ $+ $asctime $+ ] Sent: !net to all bots
  }
}

alias antirc.docker {
  if ($connected) {
    msg $antirc.channel !docker
    aline -p @AntiRC_Log [ $+ $asctime $+ ] Sent: !docker to all bots
  }
}

alias antirc.alerts {
  if ($connected) {
    msg $antirc.channel !alerts
    aline -p @AntiRC_Log [ $+ $asctime $+ ] Sent: !alerts to all bots
  }
}

alias antirc.update {
  if ($connected) {
    msg $antirc.channel !update
    aline -p @AntiRC_Log [ $+ $asctime $+ ] Sent: !update to all bots
  }
}

alias antirc.upgrade {
  if ($connected) {
    ; Ask for confirmation
    var %confirm $input(Do you want to run apt upgrade on ALL servers?,y,Confirm Upgrade)
    if (%confirm) {
      msg $antirc.channel !upgrade --force
      aline -p @AntiRC_Log [ $+ $asctime $+ ] Sent: !upgrade --force to all bots
    }
  }
}

alias antirc.broadcast {
  if ($connected) {
    var %msg $input(Enter message to broadcast to all servers:,e,Broadcast)
    if (%msg) {
      msg $antirc.channel $eval(%msg,0)
      aline -p @AntiRC_Log [ $+ $asctime $+ ] Broadcast: %msg
    }
  }
}

; ========== RESPONSE PARSING ==========
on *:TEXT:*!status*:#: {
  if ($nick == $me) return
  ; Parse status responses from bots
  if ($regex($1-,/\[(.+?)\] Status:/i)) {
    var %server $regml(1)
    var %line $line(@AntiRC_Status,0)

    ; Extract data from response lines
    var %cpu $iif($regex($1-,/CPU: ([\d.]+)%/),$regml(1),N/A)
    var %ram $iif($regex($1-,/RAM: .+? \((\d+)%\)/),$regml(1),N/A)
    var %disk $iif($regex($1-,/Disk: (\d+)%/),$regml(1),N/A)
    var %load $iif($regex($1-,/Load: ([\d.]+)/),$regml(1),N/A)

    ; Update or add line
    var %found $false
    var %i 1
    while (%i <= $line(@AntiRC_Status,0)) {
      if ($regex($line(@AntiRC_Status,%i),/^ $+ %server $+ /i)) {
        rline @AntiRC_Status %i %server $chr(9) $antirc.statuscolor(%cpu) $chr(9) %cpu $+ % $chr(9) %ram $+ % $chr(9) %disk $+ % $chr(9) %load $chr(9) $asctime
        %found = $true
        break
      }
      inc %i
    }
    if (!%found) {
      aline -p @AntiRC_Status %server $chr(9) $antirc.statuscolor(%cpu) $chr(9) %cpu $+ % $chr(9) %ram $+ % $chr(9) %disk $+ % $chr(9) %load $chr(9) $asctime
    }
  }
}

on *:TEXT:*!alerts*:#: {
  if ($nick == $me) return
  ; Parse alert responses
  if ($regex($1-,/Failed password|authentication failure|NOT in sudoers/i)) {
    aline -p @AntiRC_Alerts [ $+ $asctime $+ ] [ $+ $nick $+ ] $1-
    ; Flash window for critical alerts
    if ($regex($1-,/Failed password for root|invalid user/i)) {
      flash -r @AntiRC_Alerts
    }
  }
}

on *:TEXT:*Auto-update complete*:#: {
  if ($nick == $me) return
  aline -p @AntiRC_Log [ $+ $asctime $+ ] [ $+ $nick $+ ] $1-
  echo -a  Auto-update report from $nick : $1-
}

on *:TEXT:*Auto-update FAILED*:#: {
  if ($nick == $me) return
  aline -p @AntiRC_Alerts [ $+ $asctime $+ ] [ $+ $nick $+ ] $1-
  flash -r @AntiRC_Alerts
  echo -a  Auto-update FAILED on $nick : $1-
}

; ========== HELPERS ==========
alias antirc.statuscolor {
  if ($1 isnum) {
    if ($1 < 50) return  $+ $1 $+ %
    if ($1 < 80) return  $+ $1 $+ %
    return  $+ $1 $+ %
  }
  return N/A
}

; ========== MENU ==========
menu @AntiRC_Status {
  Refresh Status:antirc.status
  Check Disk:antirc.disk
  Check Services:antirc.services
  Check Network:antirc.net
  Check Docker:antirc.docker
  -
  Check Updates:antirc.update
  Run Upgrade:antirc.upgrade
  -
  Broadcast Message:antirc.broadcast
}

menu @AntiRC_Alerts {
  Refresh Alerts:antirc.alerts
  Clear Alerts:clear @AntiRC_Alerts
}

menu @AntiRC_Log {
  Clear Log:clear @AntiRC_Log
}

; ========== POPUP MENU (Channel) ==========
menu channel {
  AntiRC
  .Status:antirc.status
  .Disk:antirc.disk
  .Services:antirc.services
  .Network:antirc.net
  .Docker:antirc.docker
  .Alerts:antirc.alerts
  .-
  .Update Check:antirc.update
  .Upgrade:antirc.upgrade
  .-
  .Broadcast:antirc.broadcast
}

; ========== KEYBOARD SHORTCUTS ==========
alias F5 antirc.status
alias F6 antirc.alerts
alias F7 antirc.update
alias F8 antirc.disk
