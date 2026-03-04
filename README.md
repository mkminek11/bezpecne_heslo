# 7W Web MVP

MVP web aplikace inspirované hrou 7 Wonders:
- každý hráč má vlastní soukromou obrazovku (telefon),
- společná veřejná tabule je na dalším zařízení (tablet/TV).

## Co umí MVP

- Lobby: vytvoření místnosti, připojení hráčů, start hry hostitelem
- Realtime synchronizace přes Socket.IO
- Soukromý pohled hráče: vlastní ruka karet, volba akce, přehled stavu
- Veřejná tabule: vyložené karty všech, mince, armáda, skóre, log událostí
- Herní tok přes 3 věky a 6 kol/vek, rotace ruky, jednoduché bodování

## Spuštění

1. Nainstaluj Node.js 20+ (obsahuje npm):
   - https://nodejs.org/
2. V kořenu projektu spusť:

```bash
npm install
npm start
```

3. Otevři:
   - Lobby: `http://localhost:3000/`
   - Veřejná tabule: `http://localhost:3000/board.html?room=KOD`

## Poznámka

Toto je hratelný MVP prototyp „ve stylu 7 Wonders“, ne kompletní 1:1 implementace všech oficiálních pravidel a efektů karet.
