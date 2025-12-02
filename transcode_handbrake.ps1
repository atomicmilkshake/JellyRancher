$input = "L:\#MEDIA\Movies\BARBIE_MERMAID_TALE_DVD9"
$output = "L:\#MEDIA\Movies\Barbie in A Mermaid Tale (2010)\Barbie in A Mermaid Tale (2010) - SD HEVC HandBrake.mkv"
& "V:\JellyRancher\handbrake-cli\HandBrakeCLI.exe" -i $input -o $output --title 2 --preset "H.265 NVENC 1080p" --format av_mkv