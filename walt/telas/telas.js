// Telas do iPhone (Ajustes, iOS 26) usadas nos vídeos do Walt.
// row: {l: rótulo, ic: [cor, glifo], v: valor, to: tela destino, tog: true/false, chk: true/false, red: botão vermelho, sub: texto menor}
// grupo: {h: cabeçalho, f: rodapé, rows: [...], cls: classe extra}
const C = {gray:'#8E8E93', blue:'#007AFF', red:'#FF3B30', green:'#34C759', orange:'#FF9500', purple:'#5856D6', indigo:'#5E5CE6', pink:'#FF2D55', teal:'#30B0C7', yellow:'#FFCC00', dark:'#1C1C1E'};
const TELAS = {
  settings: {titulo: 'Settings', grande: true, busca: true, perfil: true, grupos: [
    {rows: [{l:'Wi-Fi', ic:[C.blue,'◉'], v:'Home'}, {l:'Bluetooth', ic:[C.blue,'ᛒ'], v:'On'}, {l:'Cellular', ic:[C.green,'▮'],}, {l:'Battery', ic:[C.green,'▭']}]},
    {rows: [{l:'General', ic:[C.gray,'⚙'], to:'general'}, {l:'Accessibility', ic:[C.blue,'♿']}, {l:'Camera', ic:[C.gray,'◎']}, {l:'Control Center', ic:[C.gray,'☰']}, {l:'Display & Brightness', ic:[C.blue,'☀']}, {l:'Home Screen & App Library', ic:[C.indigo,'▦']}, {l:'Search', ic:[C.gray,'⌕']}, {l:'Siri', ic:[C.dark,'◐']}, {l:'StandBy', ic:[C.dark,'◑']}, {l:'Wallpaper', ic:[C.teal,'✿']}]},
    {rows: [{l:'Notifications', ic:[C.red,'●'], to:'notifications'}, {l:'Sounds & Haptics', ic:[C.pink,'♪']}, {l:'Focus', ic:[C.indigo,'☾']}, {l:'Screen Time', ic:[C.indigo,'⧗']}]},
    {rows: [{l:'Face ID & Passcode', ic:[C.green,'☺']}, {l:'Emergency SOS', ic:[C.red,'SOS']}, {l:'Privacy & Security', ic:[C.blue,'✋'], to:'privacy'}]},
    {rows: [{l:'Game Center', ic:[C.pink,'◈']}, {l:'iCloud', ic:[C.blue,'☁']}, {l:'Wallet & Apple Pay', ic:[C.dark,'▤']}]},
    {rows: [{l:'Apps', ic:[C.purple,'▦'], to:'apps'}]},
  ]},
  privacy: {titulo: 'Privacy & Security', voltar: 'Settings', grupos: [
    {rows: [{l:'Location Services', ic:[C.blue,'➤'], v:'On', to:'location'}, {l:'Tracking', ic:[C.orange,'⇢'], to:'tracking'}]},
    {rows: [{l:'Calendars', ic:[C.red,'▦']}, {l:'Contacts', ic:[C.gray,'☺']}, {l:'Files & Folders', ic:[C.blue,'▤']}, {l:'Health', ic:[C.pink,'♥']}, {l:'Microphone', ic:[C.orange,'◖']}, {l:'Photos', ic:[C.yellow,'✿']}, {l:'Camera', ic:[C.gray,'◎']}]},
    {rows: [{l:'Safety Check', ic:[C.blue,'☂']}, {l:'Sensitive Content Warning', ic:[C.blue,'◬'], v:'Off'}]},
    {rows: [{l:'Analytics & Improvements', ic:null, to:'analytics'}, {l:'Apple Advertising', ic:null, to:'ads'}], cls:'noicon'},
    {rows: [{l:'Record App Activity', ic:null}], cls:'noicon'},
    {rows: [{l:'Lockdown Mode', ic:null, v:'Off'}], cls:'noicon'},
  ]},
  analytics: {titulo: 'Analytics & Improvements', voltar: 'Privacy & Security', grupos: [
    {rows: [{l:'Share iPhone Analytics', tog:true}], f:'Help Apple improve its products and services by automatically sending daily diagnostic and usage data.'},
    {rows: [{l:'Share iCloud Analytics', tog:true}, {l:'Improve Health & Activity', tog:false}, {l:'Improve Siri & Dictation', tog:false}]},
    {rows: [{l:'Analytics Data', to:null}]},
  ]},
  location: {titulo: 'Location Services', voltar: 'Privacy & Security', grupos: [
    {rows: [{l:'Location Services', tog:true}], f:'Location Services uses GPS, Bluetooth, and Wi-Fi to determine your approximate location.'},
    {rows: [{l:'Location Alerts'}]},
    {rows: [{l:'Share My Location'}]},
    {rows: [{l:'Camera', ic:[C.gray,'◎'], v:'While Using'}, {l:'Maps', ic:[C.green,'➤'], v:'While Using'}, {l:'Photos', ic:[C.yellow,'✿'], v:'Never'}, {l:'Siri', ic:[C.dark,'◐'], v:'Ask'}, {l:'Weather', ic:[C.blue,'☁'], v:'Always'}, {l:'Find My', ic:[C.green,'◉'], v:'While Using'}, {l:'System Services', ic:[C.gray,'⚙'], to:'sysservices'}]},
  ]},
  sysservices: {titulo: 'System Services', voltar: 'Location Services', grupos: [
    {rows: [{l:'Cellular Network Search', tog:true}, {l:'Compass Calibration', tog:true}, {l:'Emergency Calls & SOS', tog:true}, {l:'Find My iPhone', tog:true}, {l:'HomeKit', tog:true}, {l:'Location-Based Alerts', tog:true}, {l:'Networking & Wireless', tog:true}, {l:'Setting Time Zone', tog:true}, {l:'System Customization', tog:true}]},
    {rows: [{l:'Significant Locations & Routes', v:'On', to:'siglocs'}]},
    {h:'Product Improvement', rows: [{l:'iPhone Analytics', tog:true}, {l:'Routing & Traffic', tog:true}]},
  ]},
  siglocs: {titulo: 'Significant Locations & Routes', voltar: 'System Services', grupos: [
    {rows: [{l:'Significant Locations & Routes', tog:true}], f:'Allow iPhone to learn places and routes significant to you. This data is stored on your device.'},
    {h:'Records', cls:'records', rows: [{l:'Home', sub:'214 visits · Today'}, {l:'Pharmacy', sub:'31 visits · Yesterday'}, {l:"Doctor's Office", sub:'12 visits · Nov 18'}, {l:'Church', sub:'48 visits · Sunday'}, {l:'Grocery Store', sub:'66 visits · Nov 22'}], cls2:'plain'},
    {rows: [{l:'Clear History…', red:true}], cls:'plain'},
  ]},
  ads: {titulo: 'Apple Advertising', voltar: 'Privacy & Security', grupos: [
    {rows: [{l:'Personalized Ads', tog:true}], f:'Turning off Personalized Ads will limit Apple’s ability to deliver relevant ads to you. It does not reduce the number of ads you receive.'},
    {rows: [{l:'View Ad Targeting Information'}]},
  ]},
  tracking: {titulo: 'Tracking', voltar: 'Privacy & Security', grupos: [
    {rows: [{l:'Allow Apps to Request to Track', tog:true}], f:'Allow apps to ask to track your activity across other companies’ apps and websites.'},
    {rows: [{l:'Coupons Daily', ic:[C.orange,'%'], tog:true}, {l:'Puzzle Garden', ic:[C.green,'✿'], tog:true}, {l:'Weather Plus', ic:[C.blue,'☁'], tog:false}]},
  ]},
  apps: {titulo: 'Apps', voltar: 'Settings', grupos: [
    {rows: [{l:'Default Apps', ic:[C.gray,'✓']}, {l:'Hidden Apps', ic:[C.gray,'◌']}]},
    {rows: [{l:'App Store', ic:[C.blue,'A']}, {l:'Books', ic:[C.orange,'▤']}, {l:'Calendar', ic:[C.red,'26']}, {l:'Camera', ic:[C.gray,'◎']}, {l:'Clock', ic:[C.dark,'◷']}, {l:'Contacts', ic:[C.gray,'☺']}, {l:'FaceTime', ic:[C.green,'▶']}, {l:'Files', ic:[C.blue,'▤']}, {l:'Health', ic:[C.pink,'♥']}, {l:'Mail', ic:[C.blue,'✉']}, {l:'Maps', ic:[C.green,'➤']}, {l:'Messages', ic:[C.green,'✉'], to:'messages'}, {l:'Music', ic:[C.pink,'♪']}, {l:'Notes', ic:[C.yellow,'✎']}, {l:'Phone', ic:[C.green,'✆'], to:'phone'}, {l:'Photos', ic:[C.yellow,'✿']}, {l:'Safari', ic:[C.blue,'◎']}, {l:'Weather', ic:[C.blue,'☁']}]},
  ]},
  phone: {titulo: 'Phone', voltar: 'Apps', grupos: [
    {rows: [{l:'My Number', v:'+1 (555) 010-2468'}]},
    {h:'Calls', rows: [{l:'Respond with Text'}, {l:'Call Forwarding'}, {l:'Call Waiting'}, {l:'Show My Caller ID'}]},
    {h:'Screening', rows: [{l:'Screen Unknown Callers', v:'Never', to:'screencallers'}, {l:'Call Blocking & Identification'}, {l:'Blocked Contacts'}]},
    {rows: [{l:'SMS/Call Reporting'}]},
  ]},
  screencallers: {titulo: 'Screen Unknown Callers', voltar: 'Phone', grupos: [
    {rows: [{l:'Never', chk:true}, {l:'Ask Reason for Calling', chk:false}, {l:'Silence', chk:false}], f:'Silence: calls from numbers not in your contacts are silenced and sent to voicemail. Callers in your contacts still ring.'},
  ]},
  notifications: {titulo: 'Notifications', voltar: 'Settings', grupos: [
    {h:'Display As', rows: [{l:'Stack', v:''}]},
    {rows: [{l:'Scheduled Summary', v:'Off'}, {l:'Show Previews', v:'Always', to:'previews'}, {l:'Screen Sharing', v:'Notifications Off'}]},
    {h:'Siri', rows: [{l:'Announce Notifications'}, {l:'Siri Suggestions'}]},
    {h:'Notification Style', rows: [{l:'Calendar', ic:[C.red,'26'], sub:'Banners, Sounds, Badges'}, {l:'Mail', ic:[C.blue,'✉'], sub:'Banners, Sounds, Badges'}, {l:'Messages', ic:[C.green,'✉'], sub:'Banners, Sounds, Badges'}]},
  ]},
  previews: {titulo: 'Show Previews', voltar: 'Notifications', grupos: [
    {rows: [{l:'Always', chk:true}, {l:'When Unlocked', chk:false}, {l:'Never', chk:false}]},
  ]},
  general: {titulo: 'General', voltar: 'Settings', grupos: [
    {rows: [{l:'About'}, {l:'Software Update'}]},
    {rows: [{l:'AirDrop'}, {l:'AirPlay & Continuity'}, {l:'Picture in Picture'}]},
    {rows: [{l:'AutoFill & Passwords'}, {l:'Background App Refresh', to:'bgrefresh'}, {l:'Date & Time'}, {l:'Dictionary'}, {l:'Fonts'}, {l:'Keyboard'}, {l:'Language & Region'}]},
    {rows: [{l:'VPN & Device Management'}]},
    {rows: [{l:'Legal & Regulatory'}]},
    {rows: [{l:'Transfer or Reset iPhone'}, {l:'Shut Down', blue:true}]},
  ]},
  bgrefresh: {titulo: 'Background App Refresh', voltar: 'General', grupos: [
    {rows: [{l:'Background App Refresh', v:'Wi-Fi & Cellular Data', to:'bgopts'}], f:'Allow apps to refresh their content when on Wi-Fi or cellular in the background.'},
    {rows: [{l:'Books', ic:[C.orange,'▤'], tog:true}, {l:'Coupons Daily', ic:[C.orange,'%'], tog:true}, {l:'Mail', ic:[C.blue,'✉'], tog:true}, {l:'Maps', ic:[C.green,'➤'], tog:true}, {l:'Puzzle Garden', ic:[C.green,'✿'], tog:true}, {l:'Weather', ic:[C.blue,'☁'], tog:true}]},
  ]},
  bgopts: {titulo: 'Background App Refresh', voltar: 'Back', grupos: [
    {rows: [{l:'Off', chk:false}, {l:'Wi-Fi', chk:false}, {l:'Wi-Fi & Cellular Data', chk:true}]},
  ]},
  messages: {titulo: 'Messages', voltar: 'Apps', grupos: [
    {h:'Allow Messages to Access', rows: [{l:'Siri & Search', ic:[C.dark,'◐']}, {l:'Notifications', ic:[C.red,'●'], sub:'Banners, Sounds, Badges'}]},
    {rows: [{l:'iMessage', tog:true}, {l:'Shared with You', v:'On'}, {l:'Show Contact Photos', tog:true}, {l:'Text Message Forwarding'}]},
    {rows: [{l:'Send Read Receipts', tog:false}, {l:'Send as Text Message', tog:true}, {l:'Show Subject Field', tog:false}]},
    {h:'Message Filtering', rows: [{l:'Screen Unknown Senders', tog:false}, {l:'Filter Spam', tog:true}], f:'Sort messages from people who are not in your contacts into a separate list.'},
  ]},
};
const HOME_APPS = [
  ['FaceTime',C.green,'▶'],['Calendar','#fff','26'],['Photos','#fff','✿'],['Camera',C.gray,'◎'],
  ['Mail',C.blue,'✉'],['Notes',C.yellow,'✎'],['Reminders','#fff','☰'],['Clock',C.dark,'◷'],
  ['Weather',C.blue,'☁'],['Maps',C.green,'➤'],['Health','#fff','♥'],['Wallet',C.dark,'▤'],
  ['App Store',C.blue,'A'],['Books',C.orange,'▤'],['Contacts',C.gray,'☺'],['Settings','#8E8E93','⚙'],
];
