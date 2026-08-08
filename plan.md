# Implementationsplan

## Fas: Ren studiointegration
Status: Pågår

Syfte:
- Leverera en liten, hårdvarutrogen integration för inspelning och mixning.

Bygger på:
- Produktmål, lägesmodell och teknisk ram i `blueprint.md`.

### Arbetspaket: Session och transport
Status: Verifierad

Syfte:
- Leverera en stabil minsta implementation där hårdvarulägena bevaras och Session ger grundläggande FL-transport.

Scope:
- Ingår: Session-växling, Play, Stop Clip, utgång till Note/Chord/Custom och LED-feedback för dessa kontroller.
- Ingår inte: mixer-grid, Record, Capture MIDI, Device och övriga mixerlägen.

#### Jobbpass: Ren kärna
Status: Verifierad

Mål:
- Skapa och installera en minimal ersättare för huvudskriptets läges- och transportlogik.

Verifiering:
- Lokala enhetstester för lägesövergångar, transport och DAW-portens direkta hårdvarukommunikation.
- Användaren verifierar Session, Play, Stop Clip, Note, Chord och Custom på hårdvaran i FL Studio.

##### Steg

- [x] Definiera dokumenterade MK3-meddelanden och SysEx-kommandon.
- [x] Implementera en minimal state machine för hårdvarulägena.
- [x] Implementera Play och Stop Clip mot FL:s transport-API.
- [x] Implementera Record på CC 10 med statusstyrd LED-feedback.
- [x] Implementera dokumenterad flashing-feedback mellan svart och ljusfärg för aktiv Play och Record.
- [x] Implementera LED-feedback för leveransens kontroller.
- [x] Lägg till och kör avgränsade tester.
- [x] Installera MVP:n i de aktiva FL-scriptmapparna.
- [x] Implementera och hårdvaruverifiera diagnostiska palettvyer för färgval.
- [x] Verifiera MVP:n på hårdvaran i FL Studio.

### Arbetspaket: Mixeröversikt
Status: Verifierad

Syfte:
- Visa och välja 64 färgkodade Mixer tracks i Session Modes grundvy.

#### Jobbpass: Track-grid 1–64
Status: Verifierad

Mål:
- Visa Mixer tracks 1–64 med respektive FL-färg och låt pads välja track.

Verifiering:
- Lokala tester för gridmappning, färgkonvertering, urval och återgång från diagnostikvy.
- Användaren verifierar färger och track-val via Script output → Reload.

##### Steg

- [x] Fastställ FL Mixer-API för track count, färg och val.
- [x] Implementera Mixer track-färg till Launchpad RGB.
- [x] Implementera pad-till-track-mappning.
- [x] Återställ mixeröversikten när en diagnostikvy lämnas.
- [x] Testa, installera och hårdvaruverifiera.

### Arbetspaket: Mixerfunktioner
Status: Pågår

Syfte:
- Implementera Record Arm, Mute, Solo, Volume, Pan, Sends och Track Select mot FL Mixer tracks.

#### Jobbpass: Record Arm
Status: Verifierad

##### Steg

- [x] Fastställ CC 1 och FL:s API för armeringsstatus.
- [x] Implementera lägesväxling och LED-feedback för Record Arm.
- [x] Implementera både låst och tillfällig lägesväxling för Record Arm.
- [x] Implementera armering via pads för Mixer tracks 1–64.
- [x] Testa, installera och hårdvaruverifiera.

#### Jobbpass: Mute och Solo
Status: Verifierad

##### Steg

- [x] Implementera ömsesidigt uteslutande Mute- och Solo-lägen på CC 2 och CC 3.
- [x] Implementera låst och tillfällig lägesväxling.
- [x] Implementera statusvisning och padåtgärder för Mixer tracks 1–64.
- [x] Testa, installera och hårdvaruverifiera.

#### Jobbpass: Volume
Status: Verifierad

##### Steg

- [x] Konfigurera Launchpadens inbyggda vertikala DAW-faders.
- [x] Korrigera faderlayout till layout 1/page 0 och positionsfeedback till MIDI-kanal 5 enligt layouttabellen.
- [x] Implementera volymbank från valt spår och vänster/höger bankbyte.
- [x] Hantera fader-CC direkt i DAW-scriptet mot FL:s Mixer-API.
- [x] Hantera befintliga kontroller och deras LED-feedback direkt i DAW-scriptets Volume-vy.
- [x] Återställ alltid mixergrundvyn vid Session och rensa kvarvarande Volume-LED vid utgång.
- [x] Begränsa Volume-faders till existerande spår och visa banknavigation med pilar och Track Select.
- [x] Eliminera den cirkulära scriptbryggan genom att flytta hela Session-kontrollern till DAW-porten.
- [x] Testa, installera och hårdvaruverifiera.
