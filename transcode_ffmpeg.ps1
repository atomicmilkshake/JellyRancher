$input = "L:\#MEDIA\Movies\BARBIE_MERMAID_TALE_DVD9\VIDEO_TS\VTS_01_1.VOB"
$output = "V:\JellyRancher\BARBIE_MERMAID_TALE_1080p.mp4"
ffmpeg -i $input -c:v libx265 -preset medium -crf 23 -vf scale=1920:1080 -c:a aac -b:a 192k -movflags +faststart $output