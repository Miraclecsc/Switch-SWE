I have this in /work/w03: Introduce packaging.tags Add support for PEP 425: Compatibility Tags for Built Distributions. Closes #83

pip's version of the SOABI fallback code is more elaborate – if `get_config_var` returns None then it tries to sniff some other way. Is removing those fallbacks intentional?

Yes, somewhat. I didn't find a problem with the config vars so I assumed it was a hold-over from pre-2.7 days. So if there's a need to add them back in I can, but I'm trying to modernize this code to have less baggage to make it easier to maintain.