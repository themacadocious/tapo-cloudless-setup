# Credits

This project is a writeup and a couple of thin convenience scripts on top of
substantial prior work by others. None of the hard reverse engineering is mine.

## AI assistance

The protocol legwork, scripting, and much of the trial-and-error for this setup
was done with heavy help from **GLM 5.3** (the AI model). I'm stating that plainly
— I didn't work all of this out unaided, and the people whose research this builds
on (below) deserve the real credit for the hard parts.

## Prior work this stands on

- **[kennedn/tapo-onboarding](https://github.com/kennedn/tapo-onboarding)** — the
  bash onboarding scripts, the default-password discovery, the AP-mode protocol
  details, and the MITM-derived onboarding call sequence. The static
  `pubkey_third_account.pem` comes from here. Blog post: "Wanted to spy on my
  dog..." Start here.
- **[JurajNyiri/PyTapo](https://github.com/JurajNyiri/pytapo)** — the
  authoritative Python library: KLAP/TPAP transports, v3 login, and 200+ method
  schemas for current Tapo firmware. This is what makes the settings API usable.
- **[freeKC/tapo-v4-protocol](https://github.com/freekc/tapo-v4-protocol)** —
  documentation of the newer V4 / SPAKE2+ login (not needed for v3 cameras like
  the C217, but the reference for models that have moved to V4).

## The default password

The factory-default admin password (`TPL075526460603`) is **already public** —
it is documented in the projects above and in multiple independent writeups. It
is reproduced here only because the method is useless without naming it. It is a
factory default on your own device, not a secret.

## License

Code and docs in this repo are MIT-licensed (see [LICENSE](LICENSE)). The
upstream projects are under their own licenses — consult each repo.
