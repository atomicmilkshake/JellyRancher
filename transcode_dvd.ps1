$input = "L:\#MEDIA\Movies\BARBIE_MERMAID_TALE_DVD9"
$output = "V:\JellyRancher\BARBIE_MERMAID_TALE_1080p.mp4"
& "V:\JellyRancher\handbrake-cli\HandBrakeCLI.exe" -i $input -o $output --title 0 --encoder x265 --quality RF=23 --width 1920 --height 1080 --audio 1 --aencoder aac --ab 192 --format mp4