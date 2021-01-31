# broadlink-AC-CodesTool

Python CLI toool to generate IR climate codes table. Currently the generated files are compatible with SmartIR.
Keep in mind you can only use the operation modes supported by home assistant climate component: **cool, heat, heat_cool, auto, dry and fan_only** . As far as I can tell SmartIR doesn't support swing or preset modes (Eco, comfort, sleep, etc.) but im working on solution for it read more at the end of the page.
**SmartIR now has swing support (still no preset modes), this tool can now also generate files with swing support and a feature for adding swing support to an existing json file is coming soon.**

## Instalation

1.  install python
2.  install broadlink library
    pip install broadlink
3.  Download Python file from github

## Usage

- run python file and follow instructions given by the script, JSON file will be generated in the directory where the python file is located.

### Roadmap

(please keep in mind this was originally very quickly put together to be used only by me and its my first time sharing software online. There might be a lot of issues, they will be fixed in the near future. All feedback is welcome.)

1.  New features:
    - Continue from an unfinished json file
    - Edit finished json file
2.  Create GUI.

## Preset modes support

Im working on making either a custom component or an appdaemon app to implement presets modes for broadlink controller ac. I just started reading home assistant docs on creating integrations so it might take a while.
I would like to comment that if you're interested in this keep in mind that given the nature of AC ir controllers using swing or preset modes will exponetially increase the amount of codes you neet to record.
Using all 6 operations modes with an AC that goes from 16° to 30°C has 4 fan speeds plus vertical swing plus a couple preset modes would require you to record 2160 codes. But I live in a hot climate so I only use cool and dry modes,
I only use temperature from 19° to 26°C and I also only use one preset mode wich would require only 256 codes. So if you're in a situation like mine where you only need a subset of operation modes and temperatures but want swing fucntionality and presets
this will probably be for you. If your looking for a solution to enable 100% of your AC functionality you should probably look for an AC with WI-FI integration but if you really want to record 2k codes: go for it! It will be possible.
