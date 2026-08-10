# Blueprint

## Produktmål

Projektet skall ge Launchpad Pro MK3 en begriplig och hårdvarutrogen integration med FL Studio för studioinspelning och mixning. En kontrolls funktion skall kunna förutses från dess tryckta namn och det aktiva hårdvaruläget.

Live performance ingår inte. En framtida performance-integration skall vara ett separat skript.

## Lägesmodell

### Hårdvarulägen

Note, Chord, Custom, Sequencer, Projects och Setup hanteras i huvudsak av Launchpadens firmware. FL Studio fungerar som mottagare av musikalisk MIDI och som MIDI-klocka där det är relevant.

### Session Mode

Session Mode är FL Studios kontrollager. DAW-scriptet använder Launchpadens dokumenterade DAW Session-layout för kontroller och LED-feedback.

- Session växlar in i och ut ur FL-kontrollagret.
- Session återställer alltid kontrollagrets mixergrundvy oavsett föregående vy.
- Note, Chord och Custom lämnar Session Mode till motsvarande hårdvaruläge.
- Play styr FL Studios uppspelning.
- Record styr FL Studios globala inspelningsläge och visar mörkrött inaktiv samt ljusrött aktiv.
- Aktiv Play och Record använder Launchpadens flashing-läge mellan svart och respektive ljusfärg; inaktiva tillstånd är statiska.
- Stop Clip stoppar FL Studios uppspelning.
- 8×8-rutnätets grundvy visar 64 färgkodade Mixer tracks och väljer spår.
- Det aktiva Mixer-spårets pad visar palettfärg 3 tills ett annat spår väljs.
- Record Arm, Mute, Solo, Volume, Pan och Sends arbetar mot FL Studios Mixer tracks.
- Record Arm på CC 1 växlar ett armeringsläge där armerade spår visas med palettfärg 6 och övriga med spårfärg.
- Record Arm-läget kan låsas med ett kort tryck eller visas tillfälligt medan CC 1 hålls nedtryckt.
- Mute på CC 2 och Solo på CC 3 använder samma låsta och tillfälliga lägesmodell; mutade pads visas med 45 och solo-pads med 13.
- Volume på CC 4 använder åtta inbyggda DAW-faders, automatisk bank från valt spår och vänster/höger för bankbyte.
- Volume visar endast faders för existerande Mixer tracks. Vald track är ljus lime 17, armed tracks ljust guld 61, muted tracks mörkgrå 1 och övriga tracks vita 3. Navigerbara pilar är tända; Track Select CC 101–108 visar tillgängliga åttagrupper mörkgrått 1 och aktuell grupp ljust lime 17.
- Volume-vyn behåller befintliga transport-, mixer- och hårdvarulägesknappar samt deras LED-feedback direkt på DAW-porten.
- Mixerlägesknapparna CC 1–4 släcks utanför Session, och byte från Volume till ett annat mixerläge bevarar mål-läget efter hårdvarans layoutbekräftelse.
- Mixerlägesknapparna Record Arm, Mute, Solo och Volume släcks vid initiering och varje bekräftad hårdvarulayout utanför Session/Fader.
- Track Select används som gruppval och gruppindikering i Volume-vyn; Mixer tracks väljs i 8×8-grundvyn.
- Track Select CC 101–108 släcks i alla andra vyer än Volume.
- Setup-layouten behandlas som tillfällig; aktiv Session-mixervy bevaras och återställs när hårdvaran återgår.
- Shift + Record Arm utför Undo och Shift + Mute utför Redo i Session-vyer; respektive åtgärdsknapp visar vit 3 i minst 100 ms.
- Shift + Solo (Click) växlar FL Studios metronom och använder samma tidsstyrda vita feedback.
- Fixed Length på CC 30 växlar Pattern/Song och visar aktuell FL-status med 61 för Pattern och 17 för Song.
- Volume uppdaterar faderfärger via DAW-kanal 6; faderbanken definieras endast när vyn öppnas eller banken byts.
- Övriga märkta funktioner får endast en FL-funktion när motsvarigheten är tillräckligt nära och säker.

## Funktionsprinciper

- Märkta kontroller skall ha direkt, konsekvent och synlig betydelse.
- En kontroll utan tillräckligt nära FL-motsvarighet lämnas åt hårdvaran eller är inaktiv.
- LED-feedback visar aktivt läge och relevant FL-tillstånd.
- Ohanterade musikaliska MIDI-meddelanden lämnas vidare till FL Studio.
- Projektändrande kommandon utlöses inte av otydliga eller odokumenterade kombinationer.

## Teknisk ram

- DAW-scriptet äger Session, transport, mixerlägen, LED-feedback och DAW-faders direkt på LPProMK3 DAW-porten.
- MIDI-scriptet är ett minimalt passthrough-script för musikalisk MIDI; ingen `receiveFrom`- eller dispatch-relation finns mellan Studio-skripten.
- Implementation och tester skrivs i Python utan externa runtime-beroenden.
- Hårdvarukommunikation följer Launchpad Pro MK3:s dokumenterade MIDI- och SysEx-protokoll.
- Repot innehåller endast den självständiga studioimplementationen och dess tester.

## Verifiering

- Logik verifieras med lokala tester och stubbar för FL Studios moduler.
- Hårdvarubeteende verifieras stegvis i FL Studio.
- Ett nytt funktionsområde aktiveras först när föregående område är stabilt.
- Diagnostiska palettvyer nås tills vidare via CC 29 för färgerna 0–63 och CC 19 för färgerna 64–127.
