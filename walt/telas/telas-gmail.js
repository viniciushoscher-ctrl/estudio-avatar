// Telas do vídeo 2 (Gmail no iPhone + Safari na Conta Google). Caminhos e nomes conferidos na Ajuda do Gmail para
// iPhone (27/11/2026): Menu > Settings > General > Data privacy > Smart features; Data privacy > Google Workspace smart
// features > "Smart features in Google Workspace" / "Smart features in other Google products" > Done;
// Menu > Settings > Inbox > Email preferences > Images > "Ask before displaying external images".
// A ordem das outras linhas de cada tela é ilustrativa. Conta exibida: fictícia, endereço mascarado.
const C = {gray:'#8E8E93', blue:'#007AFF', red:'#FF3B30', green:'#34C759', orange:'#FF9500', purple:'#5856D6', indigo:'#5E5CE6', pink:'#FF2D55', teal:'#30B0C7', yellow:'#FFCC00', dark:'#1C1C1E', gblue:'#0B57D0'};
const AV = (l, c) => `<div class="gav" style="background:${c}">${l}</div>`;
const MAILS = [
  ['Mary Collins','8:12 AM','Sunday dinner','Bring the pie dish if you still have it...','#7B1FA2','M'],
  ['Pharmacy Rx','7:40 AM','Your prescription is ready','Pick up at the counter any time after 10...','#00897B','P'],
  ['Garden Deals Weekly','Yesterday','This week only: 40% off seeds','Spring is coming. Fill your garden for less...','#689F38','G', 'images'],
  ['First Hometown Bank','Yesterday','Urgent: your account will be locked','Dear valued customer, we noticed unusual...','#C62828','F', 'phish'],
  ['Tom (grandson)','Nov 24','Photos from the game!','Grandpa, here are the pictures I promised...','#1565C0','T'],
  ['Church Office','Nov 23','Bake sale volunteers','Thank you to everyone who signed up for...','#EF6C00','C'],
  ['Package Tracking','Nov 22','Your order has shipped','Estimated delivery: Thursday...','#5D4037','P'],
];
function inboxHTML(){
  let h = `<div class="gtop"><div class="gsearch" data-l="search"><span class="hamb" data-l="menu" data-to="drawer"><i></i><i></i><i></i></span><span class="gs-t">Search in mail</span>${AV('W','#3949AB').replace('gav','gav sm')}</div></div>
  <div class="content gcontent"><div class="glabel">Primary</div>`;
  for(const [n,t,s,p,c,l,id] of MAILS)
    h += `<div class="mrow" data-l="${n}" data-to="${id?'mail'+id:''}">${AV(l,c)}<div class="mtx"><div class="m1"><b>${n}</b><span>${t}</span></div><div class="m2">${s}</div><div class="m3">${p}</div></div><span class="star">☆</span></div>`;
  h += `</div><div class="compose">✎&nbsp; Compose</div><div class="gnav"><span class="on">✉<sup>3</sup></span><span>▶︎</span></div>
  <div class="snack" id="snack"><span>Sent</span><b data-l="Undo">Undo</b></div>`;
  return h;
}
function drawerHTML(){
  const it = (ic, l, extra='') => `<div class="ditem ${extra}" data-l="${l}" data-to="${l==='Settings'?'settings':''}"><span class="dic">${ic}</span>${l}</div>`;
  return `<div class="dshade"></div><div class="drawer"><div class="dlogo">Gmail</div>
   ${it('▣','All inboxes')}${it('▭','Primary','sel')}${it('◈','Promotions')}${it('☺','Social')}${it('ⓘ','Updates')}
   <div class="dhdr">All labels</div>${it('☆','Starred')}${it('◷','Snoozed')}${it('➤','Sent')}${it('▤','Drafts')}${it('✉','All mail')}${it('⚠','Spam')}${it('🗑','Trash')}
   <div class="dsep"></div>${it('⚙','Settings')}${it('?','Help & feedback')}</div>`;
}
function mailHTML(tipo){
  const top = `<div class="mtop"><span class="mback">←</span><span class="micons">▤ &nbsp; 🗑 &nbsp; ✉ &nbsp; <b data-l="dots">⋯</b></span></div>`;
  if(tipo === 'images') return top + `<div class="content mcont"><div class="msubj">This week only: 40% off seeds <span class="tag">Inbox</span></div>
    <div class="msend">${AV('G','#689F38')}<div><b>Garden Deals Weekly</b> <span class="mt">Yesterday</span><div class="to">to me ▾</div></div></div>
    <div class="imgbar"><span>Images are not displayed.</span><b data-l="Display images">Display images</b></div>
    <div class="ph"><div class="phi">🖼</div></div><div class="mbody">Spring is coming! Fill your garden for less with our best-selling seed packs.</div><div class="ph sm"><div class="phi">🖼</div></div></div>`;
  // e-mail falso (banco fictício)
  return top + `<div class="content mcont"><div class="msubj">Urgent: your account will be locked <span class="tag">Inbox</span></div>
    <div class="msend" data-sign="1">${AV('F','#C62828')}<div><b>First Hometown Bank</b> <span class="mt">Yesterday</span><div class="to addr">alerts@fhb-secure-48213.top</div></div></div>
    <div class="mbody"><p data-sign="2"><b>Dear valued customer,</b></p><p>We noticed unusual activity on your account.</p>
    <p data-sign="3"><b>Your account will be locked in 24 hours</b> unless you verify your details now.</p>
    <div class="fakebtn">Verify now</div><p class="sm">First Hometown Bank Security Team</p></div></div>
    <div class="pop" id="pop"><div>Mark as unread</div><div>Move to</div><div>Snooze</div><div>Change labels</div><div>Mark important</div><div>Mute</div><div>Print</div><div data-l="Report spam">Report spam</div></div>`;
}
const SAF = url => `<div class="safbar"><div class="safurl">ᴀA &nbsp;&nbsp;<span>🔒 ${url}</span>&nbsp;&nbsp; ↻</div><div class="safic">‹ &nbsp; › &nbsp; ⇪ &nbsp; ▢ &nbsp; ⧉</div></div>`;
const GA = `<div class="gahead"><span class="gat">Google Account</span>${AV('W','#3949AB').replace('gav','gav sm')}</div>`;
const TELAS = {
  home: {titulo: 'Home Screen'},
  inbox: {titulo: 'Gmail', html: inboxHTML, cls: 'gm'},
  drawer: {titulo: 'Menu', html: drawerHTML, cls: 'gm drawerv', overlay: true},
  settings: {titulo: 'Settings', voltar: '', gm: true, grupos: [
    {rows: [{l:'w••••••@gmail.com', sub:'Walt H.', ic:['#3949AB','W']}]},
    {h:'General', rows: [{l:'Notifications'}, {l:'Data privacy', to:'dataprivacy'}, {l:'Default apps'}, {l:'Hide bottom navigation', tog:false}]},
    {h:'Inbox', rows: [{l:'Inbox customizations'}, {l:'Email preferences', to:'emailprefs'}]},
    {h:'Account', rows: [{l:'Manage your Google Account'}, {l:'Vacation responder', v:'Off'}, {l:'Mobile signature'}]},
  ]},
  dataprivacy: {titulo: 'Data privacy', voltar: '', gm: true, grupos: [
    {rows: [{l:'Smart features', tog:true, sub:'Allow Gmail, Chat and Meet to use your content and activity to provide smart features'}]},
    {rows: [{l:'Google Workspace smart features', to:'workspace', sub:'Manage Workspace smart feature settings'}]},
    {rows: [{l:'Clear search history'}]},
  ]},
  workspace: {titulo: 'Google Workspace smart features', gm: true, sheet: true, grupos: [
    {rows: [{l:'Smart features in Google Workspace', tog:true, sub:'Allow Google Workspace to use your content and activity to personalize your experience across Workspace'}]},
    {rows: [{l:'Smart features in other Google products', tog:true, sub:'Allow Google products to use your Workspace content and activity to personalize your experience'}]},
  ]},
  emailprefs: {titulo: 'Email preferences', voltar: '', gm: true, grupos: [
    {rows: [{l:'Images', v:'Always display', to:'images'}, {l:'Conversation view', tog:true}, {l:'Show sender images', tog:true}]},
    {rows: [{l:'Swipe actions'}, {l:'Smart Reply', tog:true}]},
  ]},
  images: {titulo: 'Images', voltar: '', gm: true, grupos: [
    {rows: [{l:'Always display external images', chk:true}, {l:'Ask before displaying external images', chk:false}]},
  ]},
  mailimages: {titulo: 'Email', html: () => mailHTML('images'), cls: 'gm'},
  mailphish: {titulo: 'Email', html: () => mailHTML('phish'), cls: 'gm'},
  myaccount: {titulo: 'myaccount.google.com', safari: true, html: () => GA + `<div class="gatabs"><span class="on">Home</span><span>Personal info</span><span>Data &amp; privacy</span><span data-l="Security" data-to="security">Security</span></div>
    <div class="content gacont"><div class="gawel">${AV('W','#3949AB').replace('gav','gav xl')}<h3>Walt H.</h3><p>w••••••@gmail.com</p></div>
    <div class="gacard"><b>Privacy &amp; personalization</b><p>See the data in your Google Account and choose what activity is saved</p></div>
    <div class="gacard"><b>You have security tips</b><p>Security tips found in the Security Checkup</p></div></div>` + SAF('myaccount.google.com')},
  security: {titulo: 'Security', safari: true, html: () => GA + `<div class="gatabs"><span>Home</span><span>Personal info</span><span>Data &amp; privacy</span><span class="on">Security</span></div>
    <div class="content gacont"><h2 class="gah">Security</h2>
    <div class="gacard"><b>Recent security activity</b><p>No security activity or alerts in the last 28 days</p></div>
    <div class="gacard"><b>How you sign in to Google</b>
      <div class="garow" data-l="2-Step Verification"><span>2-Step Verification</span><em class="offv">✕ 2-Step Verification is off</em></div>
      <div class="garow"><span>Passkeys and security keys</span><em>Start using passkeys</em></div>
      <div class="garow"><span>Password</span><em>Last changed Mar 4</em></div>
      <div class="garow"><span>Recovery phone</span><em>(•••) •••-••68</em></div></div>
    <div class="gacard"><b>Your devices</b><p>iPhone · this device</p></div>
    <div class="gacard" data-l="Your connections to third-party apps & services"><b>Your connections to third-party apps &amp; services</b><p>Keep track of your connections to third-party apps and services</p>
      <div class="garow"><span>Coupon Saver Daily</span></div><div class="garow"><span>Word Puzzle Fun</span></div><div class="garow"><span>Recipe Box</span></div>
      <div class="galink" data-l="See all connections" data-to="connections">See all connections ›</div></div></div>` + SAF('myaccount.google.com')},
  connections: {titulo: 'Third-party connections', safari: true, html: () => GA + `<div class="content gacont"><h2 class="gah sm">Your connections to third-party apps &amp; services</h2>
    <p class="gap">You've given these apps and services access to some of your Google Account data</p>
    <div class="gacard nopad">${[['Coupon Saver Daily','#F57C00','%','coupon'],['Word Puzzle Fun','#43A047','W'],['Recipe Box','#E53935','R'],['Photo Print Shop','#1E88E5','P'],['Garden Planner','#7CB342','G']].map(([n,c,l,to]) => `<div class="garow app" data-l="${n}" data-to="${to||''}">${AV(l,c).replace('gav','gav sq')}<span>${n}</span><em>›</em></div>`).join('')}</div></div>` + SAF('myaccount.google.com')},
  coupon: {titulo: 'Coupon Saver Daily', safari: true, html: () => GA + `<div class="content gacont"><div class="gawel">${AV('%','#F57C00').replace('gav','gav xl sq')}<h3>Coupon Saver Daily</h3></div>
    <div class="gacard"><b>Access to your Google Account</b><p>Coupon Saver Daily has access to: your name, email address and profile picture</p><p>Access given on: March 2, 2021</p>
    <div class="gabtn" data-l="Remove access">Remove access</div></div></div>` + SAF('myaccount.google.com')},
};
const HOME_APPS = [
  ['FaceTime',C.green,'▶'],['Calendar','#fff','26'],['Photos','#fff','✿'],['Camera',C.gray,'◎'],
  ['Gmail','#fff','M'],['Notes',C.yellow,'✎'],['Reminders','#fff','☰'],['Clock',C.dark,'◷'],
  ['Weather',C.blue,'☁'],['Maps',C.green,'➤'],['Health','#fff','♥'],['Wallet',C.dark,'▤'],
  ['App Store',C.blue,'A'],['Books',C.orange,'▤'],['Contacts',C.gray,'☺'],['Settings','#8E8E93','⚙'],
];
