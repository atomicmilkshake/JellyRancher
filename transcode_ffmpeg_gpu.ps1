$input = "L:\#MEDIA\Movies\BARBIE_MERMAID_TALE_DVD9\VIDEO_TS\VTS_01_1.VOB"
$output = "L:\#MEDIA\Movies\Barbie in A Mermaid Tale (2010)\Barbie in A Mermaid Tale (2010) - SD HEVC FFmpeg.mp4"
ffmpeg -i $input -c:v hevc_nvenc -preset medium -cq 23 -c:a aac -b:a 192k -movflags +faststart $output