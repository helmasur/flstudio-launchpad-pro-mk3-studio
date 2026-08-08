# Format för denna fil

- Alla beslut skall kategoriseras och föras in under en för projektet lämplig rubrik, så att det blir lätt att hitta ett beslut i efterhand.

- Varje beslut skall inledas med beslutsdatum i formatet `YYYY-MM-DD`.

- Varje beslut skall formuleras som en kort mening och får inkludera ett kort syfte, så blir det lättare att förstå varför beslutet togs.

# Produktinriktning

- 2026-08-08: Integrationen skall utgå från Launchpad Pro MK3:s avsedda hårdvarufunktioner och implementera dem i FL Studio så långt FL Studios MIDI API medger.
- 2026-08-08: Hårdvarans namngivna och annars uppenbara kontroller skall prioriteras framför speciallösningar.
- 2026-08-08: Den befintliga kodens personliga specialfunktioner får tas bort för att ge en mindre och tydligare implementation.
- 2026-08-08: Integrationen skall prioritera studions inspelnings- och mixerarbetsflöde; live performance-funktioner hör i så fall hemma i ett framtida separat skript.

# Lägesmodell

- 2026-08-08: Note, Chord och Custom skall i huvudsak förbli Launchpadens egna hårdvarulägen.
- 2026-08-08: Session Mode skall vara det huvudsakliga kontrollagret för FL Studio.
- 2026-08-08: Launchpadens funktionsknappar skall styra motsvarande FL Studio-funktioner i Session Mode; exempelvis skall Play styra FL Studios uppspelning.
- 2026-08-08: Session Modes 8×8-rutnät skall primärt styra FL Studios Playlist Performance Clips.
- 2026-08-08: Beslutet om Playlist Performance Clips ersätts; Session Mode skall prioritera mixerfunktioner för studio och inspelning.
- 2026-08-08: Record Arm, Mute, Solo, Volume, Pan och Sends skall primärt arbeta mot FL Studios Mixer tracks.
- 2026-08-08: Session Modes grundvy skall visa en färgkodad 8×8-översikt över 64 Mixer tracks där pads väljer spår.
- 2026-08-08: Stop Clip skall motsvara FL Studios globala Stop eftersom Launchpad Pro MK3 saknar en separat stoppknapp och betydelsen är närliggande.
- 2026-08-08: Sequencer och Projects skall förbli hårdvarustyrda, med FL Studio som MIDI-mottagare och MIDI-klocka.

# Utvecklingsmetod

- 2026-08-08: Befintlig funktionalitet skall först verifieras på hårdvaran och egna ändringar därefter införas stegvis.
- 2026-08-08: Den första nya leveransen skall omfatta stabil lägesväxling och transportkontroller innan Session-rutnät och mixerfunktioner införs.
- 2026-08-08: Två diagnostiska färgpalettvyer skall tills vidare behållas i Session Mode; CC 29 visar färgerna 0–63 och CC 19 visar färgerna 64–127.

# Visuell återkoppling

- 2026-08-08: Tillgängliga funktionsknappar skall använda palettfärg 2.
- 2026-08-08: Aktiv lägesknapp på övre raden skall använda palettfärg 90.
- 2026-08-08: Play skall använda palettfärg 22 i inaktivt läge och 21 under uppspelning.
- 2026-08-08: Stop Clip skall använda palettfärg 6.
- 2026-08-08: Record på CC 10 skall styra FL Studios globala Record och använda palettfärg 6 inaktiv samt 5 aktiv.
- 2026-08-08: Beslutet om pulserande Play och Record ersätts; aktiva knappar skall använda Launchpadens dokumenterade flashing-läge.
- 2026-08-08: Aktiv Play och Record skall växla mellan statisk palettfärg 0 och respektive ljusfärg.
- 2026-08-08: Det aktiva Mixer-spårets pad skall använda palettfärg 3 tills ett annat spår väljs.
- 2026-08-08: Record Arm på CC 1 skall öppna ett armeringsläge; knappen använder palettfärg 2 inaktiv och 13 aktiv, armerade pads använder 6 och övriga behåller spårfärgen.
- 2026-08-08: Record Arm skall kunna låsas med ett kort tryck eller användas som ett tillfälligt läge genom att hålla CC 1 nedtryckt.
- 2026-08-08: Mute på CC 2 och Solo på CC 3 skall följa samma låsta och tillfälliga lägesmodell som Record Arm; mutade pads använder palettfärg 45 och solo-pads 13.
- 2026-08-08: Volume på CC 4 skall använda Launchpadens inbyggda DAW-faders i banker om åtta Mixer-spår; banken utgår från valt spår och vänster/höger byter bank utan Track Select.
- 2026-08-08: Befintliga transport-, mixer- och hårdvarulägesknappar skall behålla samma funktion och LED-feedback i Volume-vyn via DAW-bryggan.
- 2026-08-08: Session-knappen skall alltid återställa Session Modes mixergrundvy, oavsett föregående vy.
- 2026-08-08: Beslutet om dubbelriktad MIDI/DAW-brygga ersätts; DAW-scriptet skall ensamt äga Session-kontroller och MIDI-scriptet skall endast lämna musikalisk MIDI vidare.
- 2026-08-08: Track control-raden CC 1–8 skall endast vara tänd i Session-vyer; byte från Volume till Record Arm, Mute eller Solo skall bevara det valda mixerläget.
- 2026-08-08: Record Arm, Mute, Solo och Volume på CC 1–4 skall alltid vara släckta utanför Session- och Fader-vyerna.
