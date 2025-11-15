#!/usr/bin/env python3
"""
Parse the archived Looney Tunes Cartoon Checklist and produce a chronological
JSON file containing all ~1,000 shorts with titles and release dates.

Output: scripts/._state/tv_episode_cache/looney_tunes_full_filmography.json
"""

import json
import os
import re
from datetime import datetime

# Use the archived checklist content that was fetched earlier
CHECKLIST_TEXT = """
#  Looney Tunes Cartoon Checklist

What follows is a very short and complete listing of every Warner Bros. Looney
Tunes and Merrie Melodies cartoon in order of release. This listing also includes
movies and TV specials which feature the classic characters (Bugs, Daffy,
Tweety, Porky, etc.). Some miscellaneous shorts are listed which either have a
significant link to the years of 1930-69 or which feature the famous WB characters.
This file is based upon the filmography in the book That's All, Folks!: The Art of Warner Bros. Animation by Steve Schneider. Other shorts filmography help from Looney Tunes and Merrie Melodies by Jerry Beck and Will Friedwald.

1930:
____ Sinkin' in the Bathtub
____ Congo Jazz
____ Hold Anything
____ The Booze Hangs High
____ Box Car Blues

1931:
____ The Big Man From the North
____ Ain't Nature Grand?
____ Ups 'n Downs
____ Dumb Patrol
____ Yodeling Yokels
____ Bosko's Holiday
____ The Tree's Knees
____ Lady Play Your Mandolin
____ Smile, Darn Ya, Smile
____ Bosko Shipwrecked
____ One More Time
____ Bosko the Doughboy
____ You Don't Know What You're Doin'
____ Bosko's Soda Fountain
____ Hittin' the Trail For Hallelujah Land
____ Bosko's Fox Hunt
____ Red-Headed Baby

1932:
____ Bosko at the Zoo
____ Pagan Moon
____ Battling Bosko
____ Freddy the Freshman
____ Big-Hearted Bosko
____ Crosby, Columbo, and Vallee
____ Bosko's Party
____ Goopy Geer
____ Bosko and Bruno
____ It's Got Me Again
____ Moonlight For Two
____ Bosko's Dog Race
____ The Queen Was in the Parlor
____ Bosko at the Beach
____ I Love a Parade
____ Bosko's Store
____ Bosko the Lumberjack
____ You're Too Careless With Your Kisses
____ Ride Him, Bosko!
____ I Wish I Had Wings
____ Bosko the Drawback
____ A Great Big Bunch of You
____ Bosko's Dizzy Date
____ Three's a Crowd
____ Bosko's Woodland Daze

1933:
____ The Shanty Where Santy Claus Lives
____ Bosko in Dutch
____ One Step Ahead of My Shadow
____ Bosko in Person
____ Young and Healthy
____ Bosko the Speed King
____ The Organ Grinder
____ Bosko's Knight-Mare
____ Wake Up the Gypsy in Me
____ Bosko the Sheepherder
____ I Like Mountain Music
____ Beau Bosko
____ Shuffle Off to Buffalo
____ Bosko's Mechanical Man
____ The Dish Ran Away With the Spoon
____ Bosko the Musketeer
____ We're in the Money
____ Bosko's Picture Show
____ Buddy's Day Out
____ I've Got to Sing a Torch Song
____ Buddy's Beer Garden
____ Buddy's Show Boat
____ Sittin' On a Backyard Fence

1934:
____ Buddy the Gob
____ Pettin' in the Park
____ Honeymoon Hotel
____ Buddy and Towser
____ Beauty and the Beast
____ Buddy's Garage
____ Those Were Wonderful Days
____ Buddy's Trolley Troubles
____ Goin' to Heaven on a Mule
____ Buddy of the Apes
____ How Do I Know It's Sunday?
____ Buddy's Bearcats
____ Why Do I Dream These Dreams?
____ Buddy's Circus
____ Buddy the Woodsman
____ The Miller's Daughter
____ Buddy the Detective
____ The Girl at the Ironing Board
____ Viva Buddy
____ Shake Your Powder Puff
____ Rhythm in the Bow
____ Those Beautiful Dames
____ Buddy's Adventures
____ Buddy the Dentist

1935:
____ Buddy of the Legion
____ Mr. and Mrs. is the Name
____ The Country Boy
____ Buddy's Theatre
____ I Haven't Got a Hat
____ Buddy's Pony Express
____ Along Flirtation Walk
____ Buddy in Africa
____ My Green Fedora
____ Buddy's Lost World
____ Into Your Dance
____ Buddy's Bug Hunt
____ The Country Mouse
____ Buddy Steps Out
____ The Merry Old Soul
____ Buddy the Gee Man
____ The Lady in Red
____ A Cartoonist's Nightmare
____ Hollywood Capers
____ Little Dutch Plate
____ Golddiggers of '49
____ Billboard Frolics
____ The Fire Alarm
____ Flowers For Madame

1936:
____ Plane Dippy
____ I Wanna Play House
____ Alpine Antics
____ The Phantom Ship
____ The Cat Came Back
____ Boom Boom
____ Miss Glory
____ The Blow Out
____ I'm a Big Shot Now
____ Westward Whoa!
____ Let It Be Me
____ I'd Love to Take Orders From You
____ Fish Tales
____ Bingo Crosbyana
____ Shanghaied Shipmates
____ When I Yoo Hoo
____ Porky's Pet
____ I Love to Singa
____ Porky the Rainmaker
____ Sunday Go to Meetin' Time
____ Porky's Poultry Plant
____ At Your Service Madame
____ Porky's Moving Day
____ Boulevardier From the Bronx
____ Don't Look Now
____ Little Beau Porky
____ The Coo-Coo Nut Grove
____ The Village Smithy
____ Porky in the Northwoods

1937:
____ He Was Her Man
____ Porky the Wrestler
____ Pigs is Pigs
____ Porky's Road Race
____ Picador Porky
____ I Only Have Eyes For You
____ The Fella With the Fiddle
____ Porky's Romance
____ She Was an Acrobat's Daughter
____ Porky's Duck Hunt
____ Ain't We Got Fun
____ Porky and Gabby
____ Clean Pastures
____ Uncle Tom's Bungalow
____ Porky's Building
____ Streamlined Greta Green
____ Sweet Sioux
____ Porky's Super Service
____ Egghead Rides Again
____ Porky's Badtime Story
____ Plenty of Money and You
____ Porky's Railroad
____ A Sunbonnet Blue
____ Get Rich Quick Porky
____ Speaking of the Weather
____ Porky's Garden
____ Dog Daze
____ I Wanna Be a Sailor
____ Rover's Rival
____ The Lyin' Mouse
____ The Case of the Stuttering Pig
____ Little Red Walking Hood
____ Porky's Double Trouble
____ The Woods Are Full of Cuckoos
____ Porky's Hero Agency
____ September in the Rain

1938:
____ Daffy Duck and Egghead
____ Porky's Poppa
____ My Little Buckeroo
____ Porky at the Crocadero
____ Jungle Jitters
____ What Price Porky
____ The Sneezing Weasel
____ Porky's Phony Express
____ A Star is Hatched
____ Porky's Five and Ten
____ The Penguin Parade
____ Porky's Hare Hunt
____ Now That Summer is Gone
____ Injun Trouble
____ The Isle of Pingo Pongo
____ Porky the Fireman
____ Katnip Kollege
____ Porky's Party
____ Have You Got Any Castles?
____ Love and Curses
____ Porky's Spring Planting
____ Cinderella Meets Fella
____ Porky and Daffy
____ The Major Lied Till Dawn
____ Wholly Smoke
____ A-Lad-In Bagdad
____ Cracked Ice
____ A Feud There Was
____ Porky in Wackyland
____ Little Pancho Vanilla
____ Porky's Naughty Nephew
____ Johnny Smith and Poker-Huntas
____ Porky in Egypt
____ You're an Education
____ The Night Watchman
____ The Daffy Doc
____ Daffy Duck in Hollywood
____ Porky the Gob
____ Count Me Out
____ The Mice Will Play

1939:
____ The Lone Stranger and Porky
____ Dog Gone Modern
____ It's an Ill Wind
____ Hamateur Night
____ Robin Hood Makes Good
____ Porky's Tire Trouble
____ Gold Rush Daze
____ Porky's Movie Mystery
____ A Day at the Zoo
____ Prest-o Change-o
____ Chicken Jitters
____ Bars and Stripes Forever
____ Daffy Duck and the Dinosaur
____ Porky and Teabiscuit
____ Thugs With Dirty Mugs
____ Kristopher Kolombus Jr.
____ Naughty But Mice
____ Hobo Gadget Band
____ Polar Pals
____ Believe it, or Else
____ Scalp Trouble
____ Old Glory
____ Porky's Picnic
____ The Dangerous Dan McFoo
____ Snow Man's Land
____ Wise Quacks
____ Hare-Um Scare-Um
____ Detouring America
____ Porky's Hotel
____ Little Brother Rat
____ Sioux Me
____ Jeepers Creepers
____ Land of the Midnight Fun
____ Naughty Neighbors
____ Little Lion Hunter
____ The Good Egg
____ Fresh Fish
____ Pied Piper Porky
____ Fagin's Freshman
____ Porky the Giant Killer
____ Sniffles and the Bookworm
____ The Film Fan
____ Screwball Football
____ The Curious Puppy

1940:
____ Porky's Last Stand
____ The Early Worm Gets the Bird
____ Africa Squeaks
____ Mighty Hunters
____ Ali Baba Bound
____ Busy Bakers
____ Elmer's Candid Camera
____ Pilgrim Porky
____ Cross-Country Detours
____ Confederate Honey
____ Slap-Happy Pappy
____ The Bear's Tale
____ The Hardship of Miles Standish
____ Porky's Poor Fish
____ Sniffles Takes a Trip
____ You Ought to Be in Pictures
____ A Gander at Mother Goose
____ The Chewin' Bruin
____ Tom Thumb in Trouble
____ Circus Today
____ Porky's Baseball Broadcast
____ Little Blabbermouse
____ The Egg Collector
____ A Wild Hare
____ Ghost Wanted
____ Patient Porky
____ Ceiling Hero
____ Malibu Beach Party
____ Calling Dr. Porky
____ Stage Fright
____ Prehistoric Porky
____ Holiday Highlights
____ Good Night, Elmer
____ The Sour Puss
____ Wacky Wildlife
____ Bedtime For Sniffles
____ Porky's Hired Hand
____ Of Fox and Hounds
____ The Timid Toreador
____ Shop, Look, and Listen

1941:
____ Elmer's Pet Rabbit
____ Porky's Snooze Reel
____ The Fighting 69 1/2th
____ Sniffles Bells the Cat
____ The Haunted Mouse
____ The Crackpot Quail
____ The Cat's Tale
____ Joe Glow the Firefly
____ Tortoise Beats Hare
____ Porky's Bear Facts
____ Goofy Groceries
____ Toy Trouble
____ Porky's Preview
____ The Trial of Mister Wolf
____ Porky's Ant
____ Farm Frolics
____ Hollywood Steps Out
____ A Coy Decoy
____ Hiawatha's Rabbit Hunt
____ Porky's Prize Pony
____ The Wacky Worm
____ Meet John Doughboy
____ The Heckling Hare
____ Inki and the Lion
____ Aviation Vacation
____ We, the Animals Squeak!
____ Sport Chumpions
____ The Henpecked Duck
____ Snow Time For Comedy
____ All This and Rabbit Stew
____ Notes to You
____ The Brave Little Bat
____ The Bug Parade
____ Robinson Crusoe Jr.
____ Rookie Revue
____ Saddle Silly
____ The Cagey Canary
____ Porky's Midnight Matinee
____ Rhapsody in Rivets
____ Wabbit Twouble
____ Porky's Pooch

1942:
____ Hop, Skip, and a Chump
____ Porky's Pastry Pirates
____ The Bird Came C.O.D.
____ Aloha Hooey
____ Who's Who in the Zoo?
____ Porky's Cafe
____ Conrad the Sailor
____ Crazy Cruise
____ The Wabbit Who Came to Supper
____ Saps in Chaps
____ Horton Hatches the Egg
____ Dog Tired
____ Daffy's Southern Exposure
____ The Wacky Wabbit
____ The Draft Horse
____ Nutty News
____ Lights Fantastic
____ Hobby Horse Laffs
____ Hold the Lion, Please
____ Gopher Goofy
____ Double Chaser
____ Wacky Blackouts
____ Bugs Bunny Gets the Boid
____ Foney Fables
____ The Ducktators
____ The Squawkin' Hawk
____ Eatin' On the Cuff
____ Fresh Hare
____ The Impatient Patient
____ Fox Pop
____ The Dover Boys
____ The Hep Cat
____ The Sheepish Wolf
____ The Daffy Duckaroo
____ The Hare-Brained Hypnotist
____ A Tale of Two Kitties
____ My Favorite Duck
____ Ding Dog Daddy
____ Case of the Missing Hare

1943:
____ Coal Black and de Sebben Dwarfs
____ Confusions of a Nutzy Spy
____ Pigs in a Polka
____ Tortoise Wins By a Hare
____ Fifth Column Mouse
____ To Duck or Not to Duck
____ Flop Goes the Weasel
____ Hop and Go
____ Super-Rabbit
____ The Unbearable Bear
____ The Wise-Quacking Duck
____ Greetings Bait
____ Tokio Jokio
____ Jack-Wabbit and the Beanstalk
____ The Aristo-Cat
____ Yankee Doodle Daffy
____ Wackiki Wabbit
____ Tin Pan Alley Cats
____ Porky Pig's Feat
____ Scrap Happy Daffy
____ Hiss and Make Up
____ A Corny Concerto
____ Fin N' Catty
____ Falling Hare
____ Inki and the Mynah Bird
____ Daffy the Commando
____ An Itch in Time
____ Puss N' Booty

1944:
____ Little Red Riding Rabbit
____ What's Cookin', Doc?
____ Meatless Flyday
____ Tom Turk and Daffy
____ Bugs Bunny and the Three Bears
____ I Got Plenty of Mutton
____ The Weakly Reporter
____ Tick Tock Tuckered
____ Bugs Bunny Nips the Nips
____ The Swooner Crooner
____ Russian Rhapsody
____ Duck Soup to Nuts
____ Angel Puss
____ Slightly Daffy
____ Hare Ribbin'
____ Brother Brat
____ Hare Force
____ From Hand to Mouse
____ Birdy and the Beast
____ Buckaroo Bugs
____ Goldilocks and the Jivin' Bears
____ Plane Daffy
____ Lost and Foundling
____ Booby Hatched
____ The Old Grey Hare
____ The Stupid Cupid
____ Stage Door Cartoon

1945:
____ Odor-able Kitty
____ Herr Meets Hare
____ Draftee Daffy
____ The Unruly Hare
____ Trap-Happy Porky
____ Life With Feathers
____ Behind the Meatball
____ Hare Trigger
____ Ain't That Ducky
____ A Gruesome Twosome
____ A Tale of Two Mice
____ Wagon Heels
____ Hare Conditioned
____ Fresh Airedale
____ The Bashful Buzzard
____ Peck Up Your Troubles
____ Hare Tonic
____ Nasty Quacks

1946:
____ Book Revue
____ Baseball Bugs
____ Holiday For Shoestrings
____ Quentin Quail
____ Baby Bottleneck
____ Hare Remover
____ Daffy Doodles
____ Hollywood Canine Canteen
____ Hush My Mouse
____ Hair-Raising Hare
____ Kitty Kornered
____ Hollywood Daffy
____ Acrobatty Bunny
____ The Eager Beaver
____ The Great Piggy Bank Robbery
____ Bacall to Arms
____ Of Thee I Sting
____ Walky Talky Hawky
____ Racketeer Rabbit
____ Fair and Worm-er
____ The Big Snooze
____ The Mouse-Merized Cat
____ Mouse Menace
____ Rhapsody Rabbit
____ Roughly Squeaking

1947:
____ One Meat Brawl
____ The Goofy Gophers
____ The Gay Anties
____ Scent-imental Over You
____ A Hare Grows in Manhattan
____ Birth of a Notion
____ Tweetie Pie
____ Rabbit Transit
____ Hobo Bobo
____ Along Came Daffy
____ Inki at the Circus
____ Easter Yeggs
____ Crowing Pains
____ A Pest in the House
____ The Foxy Duckling
____ House Hunting Mice
____ Little Orphan Airedale
____ Doggone Cats
____ Slick Hare
____ Mexican Joyride
____ Catch as Cats Can
____ A Horse Fly Fleas

1948:
____ Gorilla My Dreams
____ Two Gophers From Texas
____ A Feather in His Hare
____ What Makes Daffy Duck?
____ What's Brewin', Bruin?
____ Daffy Duck Slept Here
____ A Hick, a Slick, and a Chick
____ Back Alley Op-Roar
____ I Taw a Putty Tat
____ Rabbit Punch
____ Hop, Look, and Listen
____ Nothing But the Tooth
____ Buccaneer Bunny
____ Bone Sweet Bone
____ Bugs Bunny Rides Again
____ The Rattled Rooster
____ The Up-Standing Sitter
____ The Shell Shocked Egg
____ Haredevil Hare
____ You Were Never Duckier
____ Dough Ray Me-Ow
____ Hot Cross Bunny
____ The Pest That Came to Dinner
____ Hare Splitter
____ Odor of the Day
____ The Foghorn Leghorn
____ A-Lad-in His Lamp
____ Daffy Dilly
____ Kit For Cat
____ The Stupor Salesman
____ Riff Raffy Daffy
____ My Bunny Lies Over the Sea
____ Scaredy Cat

1949:
____ Wise Quackers
____ Hare Do
____ Holiday For Drumsticks
____ The Awful Orphan
____ Porky Chops
____ Mississippi Hare
____ Paying the Piper
____ Daffy Duck Hunt
____ Rebel Rabbit
____ Mouse Wreckers
____ High Diving Hare
____ The Bee-Deviled Bruin
____ Curtain Razor
____ Bowery Bugs
____ Mouse Mazurka
____ Long-Haired Hare
____ Hen House Henery
____ Knights Must Fall
____ Bad Ol' Putty Tat
____ The Grey Hounded Hare
____ Often an Orphan
____ The Windblown Hare
____ Dough For the Do-Do
____ Fast and Furry-ous
____ Each Dawn I Crow
____ Frigid Hare
____ Swallow the Leader
____ Bye, Bye, Bluebeard
____ For Scent-imental Reasons
____ Hippety Hopper
____ Which is Witch?
____ Bear Feat
____ Rabbit Hood
____ A Ham in a Role

1950:
____ Home Tweet Home
____ Hurdy Gurdy Hare
____ Boobs in the Woods
____ Mutiny On the Bunny
____ The Lion's Busy
____ The Scarlet Pumpernickel
____ Homeless Hare
____ Strife With Father
____ The Hypo-Chondri-Cat
____ Big House Bunny
____ The Leghorn Blows at Midnight
____ His Bitter Half
____ An Egg Scramble
____ What's Up, Doc?
____ All Abir-r-rd
____ 8 Ball Bunny
____ It's Hummer Time
____ Golden Yeggs
____ Hillbilly Hare
____ Dog Gone South
____ The Ducksters
____ A Fractured Leghorn
____ Bunker Hill Bunny
____ Canary Row
____ Stooge For a Mouse
____ Pop 'im Pop
____ Bushy Hare
____ Caveman Inki
____ Dog Collared
____ The Rabbit of Seville
____ Two's a Crowd

1951:
____ Hare We Go
____ A Fox in a Fix
____ Canned Feud
____ Rabbit Every Monday
____ Putty Tat Trouble
____ Corn Plastered
____ Bunny Hugged
____ Scent-imental Romeo
____ A Bone For a Bone
____ The Fair-Haired Hare
____ A Hound For Trouble
____ Early to Bet
____ Rabbit Fire
____ Room and Bird
____ Chow Hound
____ French Rarebit
____ The Wearing of the Grin
____ Leghorn Swoggled
____ His Hare-Raising Tale
____ Cheese Chasers
____ Lovelorn Leghorn
____ Tweety's S.O.S.
____ Ballot Box Bunny
____ A Bear For Punishment
____ Sleepy-Time Possum
____ Drip-Along Daffy
____ Big Top Bunny
____ Tweet, Tweet, Tweety
____ The Prize Pest

1952:
____ Who's Kitten Who?
____ Operation: Rabbit
____ Feed the Kitty
____ Gift Wrapped
____ Foxy By Proxy
____ Thumb Fun
____ 14 Carrot Rabbit
____ Little Beau Pepe
____ Kiddin' the Kitten
____ Water, Water Every Hare
____ Little Red Rodent Hood
____ Sock-a-Doodle-Do
____ Beep, Beep!
____ The Hasty Hare
____ Ain't She Tweet
____ The Turn-Tale Wolf
____ Cracked Quack
____ Oily Hare
____ Hoppy Go Lucky
____ Going! Going! Gosh!
____ A Bird in a Guilty Cage
____ Mouse Warming
____ Rabbit Seasoning
____ The Egg-Cited Rooster
____ Tree For Two
____ The Super Snooper
____ Rabbit's Kin
____ Terrier Stricken
____ Fool Coverage
____ Hare Lift

1953:
____ Don't Give Up the Sheep
____ Snow Business
____ A Mouse Divided
____ Forward March Hare
____ Kiss Me Cat
____ Duck Amuck
____ Upswept Hare
____ A Peck o' Trouble
____ Fowl Weather
____ Muscle Tussle
____ Southern Fried Rabbit
____ Ant Pasted
____ Much Ado About Nutting
____ There Auto Be a Law
____ Hare Trimmed
____ Tom-Tom Tomcat
____ Wild Over You
____ Duck Dodgers in the 24 1/2th Century
____ Bully For Bugs
____ Plop Goes the Weasel
____ Cat-Tails For Two
____ A Street Cat Named Sylvester
____ Zipping Along
____ Duck! Rabbit! Duck!
____ Easy Peckins
____ Catty Cornered
____ Of Rice and Hen
____ Cats A-Weigh
____ Robot Rabbit
____ Punch Trunk

1954:
____ Dog Pounded
____ Captain Hareblower
____ I Gopher You
____ Feline Frame-Up
____ Wild Wife
____ No Barking
____ Bugs and Thugs
____ The Cat's Bah
____ Design For Leaving
____ Bell Hoppy
____ No Parking Hare
____ Dr. Jerkyl's Hide
____ Claws For Alarm
____ Little Boy Boo
____ Devil May Hare
____ Muzzle Tough
____ The Oily American
____ Bewitched Bunny
____ Satan's Waitin'
____ Stop, Look, and Hasten
____ Yankee Doodle Bugs
____ Gone Batty
____ Goo Goo Goliath
____ By Word of Mouse
____ From A to Z-z-z-z
____ Quack Shot
____ Lumber Jack-Rabbit
____ My Little Duckaroo
____ Sheep Ahoy
____ Baby Buggy Bunny

1955:
____ Pizzicato Pussycat
____ Feather Dusted
____ Pests For Guests
____ Beanstalk Bunny
____ All Fowled Up
____ Stork Naked
____ Lighthouse Mouse
____ Sahara Hare
____ Sandy Claws
____ The Hole Idea
____ Ready, Set, Zoom!
____ Hare Brush
____ Past Perfumance
____ Tweety's Circus
____ Rabbit Rampage
____ Lumber Jerks
____ This is a Life?
____ Double or Mutton
____ Jumpin' Jupiter
____ A Kiddie's Kitty
____ Hyde and Hare
____ Dime to Retire
____ Speedy Gonzales
____ Knight-Mare Hare
____ Two Scents Worth
____ Red Riding Hoodwinked
____ Roman Legion-Hare
____ Heir Conditioned
____ Guided Muscle
____ Pappy's Puppy
____ One Froggy Evening

1956:
____ Bugs Bonnets
____ Too Hop to Handle
____ Weasel Stop
____ The High and the Flighty
____ Broom-Stick Bunny
____ Rocket Squad
____ Tweet and Sour
____ Heaven Scent
____ Mixed Master
____ Rabbitson Crusoe
____ Gee Whiz-z-z-z!
____ Tree Cornered Tweety
____ The Unexpected Pest
____ Napoleon Bunny-Part
____ Tugboat Granny
____ Stupor Duck
____ Barbary Coast Bunny
____ Rocket-Bye Baby
____ Half Fare Hare
____ Raw! Raw! Rooster
____ The Slap-Hoppy Mouse
____ A Star is Bored
____ Deduce You Say
____ Yankee Dood It
____ Wideo Wabbit
____ There They Go-Go-Go!
____ Two Crows From Tacos
____ The Honey-Mousers
____ To Hare is Human

1957:
____ The Three Little Bops
____ Tweet Zoo
____ Scrambled Aches
____ Ali Baba Bunny
____ Go Fly a Kit
____ Tweety and the Beanstalk
____ Bedevilled Rabbit
____ Boyhood Daze
____ Cheese it- the Cat!
____ Fox Terror
____ Piker's Peak
____ Steal Wool
____ Boston Quackie
____ What's Opera, Doc?
____ Tabasco Road
____ Birds Anonymous
____ Ducking the Devil
____ Bugsy and Mugsy
____ Zoom and Bored
____ Greedy For Tweety
____ Touche and Go
____ Show Biz Bugs
____ Mouse-Taken Identity
____ Gonzales' Tamales
____ Rabbit Romeo

1958:
____ Don't Axe Me
____ Tortilla Flaps
____ Hare-Less Wolf
____ A Pizza Tweety Pie
____ Robin Hood Daffy
____ Hare-Way to the Stars
____ Whoa Be-Gone!
____ A Waggily Tale
____ Feather Bluster
____ Now Hare This
____ To Itch His Own
____ Dog Tales
____ Knighty Knight Bugs
____ Weasel While You Work
____ A Bird in a Bonnet
____ Hook, Line, and Stinker
____ Pre-Hysterical Hare
____ Gopher Broke
____ Hip- Hip- Hurry!
____ Cat Feud

1959:
____ Baton Bunny
____ Mouse-Placed Kitten
____ China Jones
____ Hare-Abian Nights
____ Trick or Tweet
____ The Mouse That Jack Built
____ Apes of Wrath
____ Hot Rod and Reel
____ A Mutt in a Rut
____ Backwoods Bunny
____ Really Scent
____ Mexicali Shmoes
____ Tweet and Lovely
____ Wild and Woolly Hare
____ The Cat's Paw
____ Here Today, Gone Tamale
____ Bonanza Bunny
____ A Broken Leghorn
____ Wild About Hurry
____ A Witch's Tangled Hare
____ Unnatural History
____ Tweet Dreams
____ People are Bunny

1960:
____ The Fastest With the Mostest
____ West of the Pesos
____ Horse Hare
____ Wild Wild World
____ Goldimouse and the Three Cats
____ Person to Bunny
____ Who Scent You?
____ Hyde and Go Tweet
____ Rabbit's Feat
____ Crockett-Doodle-Do
____ Mouse and Garden
____ Ready, Woolen, and Able
____ Mice Follies
____ From Hare to Heir
____ The Dixie Fryer
____ Hopalong Casualty
____ Trip For Tat
____ Dog Gone People
____ High Note
____ Lighter Than Hare

1961:
____ Cannery Woe
____ Zip N' Snort
____ Hoppy Daze
____ The Mouse On 57th Street
____ Strangled Eggs
____ Birds of a Father
____ D' Fightin' Ones
____ The Abominable Snow Rabbit
____ Lickety-Splat!
____ A Scent of the Matterhorn
____ The Rebel Without Claws
____ Compressed Hare
____ The Pied Piper Guadalupe
____ Prince Violent (a.k.a. Prince Varmint)
____ Daffy's Inn Trouble
____ What's My Lion?
____ Beep Prepared
____ The Last Hungry Cat
____ Nelly's Folly

1962:
____ Wet Hare
____ A Sheep in the Deep
____ Fish and Slips
____ Quackodile Tears
____ Crow's Feat
____ Mexican Boarders
____ Bill of Hare
____ Zoom at the Top
____ The Slick Chick
____ Louvre Come Back to Me
____ Honey's Money
____ The Jet Cage
____ Mother Was a Rooster
____ Good Noose
____ Shiskabugs
____ Martian Through Georgia

1963:
____ I Was a Teenage Thumb
____ Devil's Feud Cake
____ Fast Buck Duck
____ The Million-Hare
____ Mexican Cat Dance
____ Now Hear This
____ Woolen Under Where
____ Hare-Breadth Hurry
____ Banty Raids
____ Chili Weather
____ The Unmentionables
____ Aqua Duck
____ Mad as a Mars Hare
____ Claws in the Lease
____ Transylvania 6-5000
____ To Beep or Not to Beep

1964:
____ Dumb Patrol
____ A Message to Gracias
____ Bartholomew Versus the Wheel
____ Freudy Cat
____ Dr. Devil and Mr. Hare
____ Nuts and Volts
____ The Iceman Ducketh
____ War and Pieces
____ Hawaiian Aye Aye
____ False Hare
____ Senorella and the Glass Huarache
____ Pancho's Hideaway
____ Road to Andalay

1965:
____ It's Nice to Have a Mouse Around the House
____ Cats and Bruises
____ The Wild Chase
____ Moby Duck
____ Assault and Peppered
____ Well Worn Daffy
____ Suppressed Duck
____ Corn On the Cop
____ Rushing Roulette
____ Run, Run, Sweet Road Runner
____ Tease For Two
____ Tired and Feathered
____ Boulder Wham!
____ Chili Corn Corny
____ Just Plane Beep
____ Hairied and Hurried
____ Go Go Amigo
____ Highway Runnery
____ Chaser On the Rocks

1966:
____ The Astroduck
____ Shot and Bothered
____ Out and Out Rout
____ Muchos Locos
____ Mexican Mouse-Piece
____ The Solid Tin Coyote
____ Clippety Clobbered
____ Daffy Rents
____ A-Haunting We Will Go
____ Snow Excuse
____ A Squeak in the Deep
____ Feather Finger
____ Swing Ding Amigo
____ Sugar and Spies
____ A Taste of Catnip

1967:
____ Daffy's Diner
____ Quacker Tracker
____ The Music Mice-Tro
____ The Spy Swatter
____ Speedy Ghost to Town
____ Rodent to Stardom
____ Go Away Stowaway
____ Cool Cat
____ Merlin the Magic Mouse
____ Fiesta Fiasco

1968:
____ Hocus Pocus Pow Wow
____ Norman Normal
____ Big Game Haunt
____ Skyscraper Caper
____ Hippydrome Tiger
____ Feud With a Dude
____ See Ya Later, Gladiator
____ 3 Ring Wing Ding
____ Flying Circus
____ Chimp and Zee
____ Bunny and Claude (We Rob Carrot Patches)

1969:
____ The Great Carrot Train Robbery
____ Fistic Mystic
____ Rabbit Stew and Rabbits Too
____ Shamrock and Roll
____ Bugged By a Bee
____ Injun Trouble

1987:
____ The Duxorcist

1988:
____ Night of the Living Duck

1990:
____ Box Office Bunny

1994:
____ Chariots of Fur

1995:
____ Carrotblanca
____ Another Froggy Evening

1996:
____ Superior Duck

1997:
____ Pullet Surprise
____ From Hare to Eternity
____ Father of the Bird

2000:
____ Little Go Beep

2004:
____ Daffy Duck For President

----------------------------------------

MISC. SHORTS:

1929:
____ Bosko the Talk-Ink Kid

1932:
____ Bosko and Honey

1949:
____ So Much For So Little

1952:
____ Orange Blossoms For Violet

1955:
____ A Hitch in Time

1956:
____ 90 Day Wandering

1957:
____ Drafty, Isn't It?

1962:
____ The Adventures of the Road Runner

1963:
____ Philbert (Three's a Crowd)

1965:
____ Road Runner A-Go-Go
____ Zip Zip Hooray

1968:
____ The Door

1979:
____ Bugs Bunny's Christmas Carol
____ Freeze Frame
____ Fright Before Christmas

1980:
____ The Yolk's On You
____ The Chocolate Chase
____ Daffy Flies North
____ Portrait of the Artist as a Young Bunny
____ Soup or Sonic
____ Spaced-Out Bunny
____ Duck Dodgers and the Return of the 24 1/2th Century

1991:
____ Blooper Bunny

1992:
____ The Invasion of the Bunny Snatchers

2003:
____ Duck Dodgers in Attack of the Drones
____ My Generation G-g-gap
____ Whizzard of Ow
____ Museum Scream
____ Cock-a-Doodle Duel

2004:
____ Hare and Loathing in Las Vegas

----------------------------------------

PRIVATE SNAFU SHORTS (MADE FOR THE U.S. ARMY):

1943:
____ Coming Snafu
____ Gripes
____ Spies
____ The Goldbrick
____ The Infantry Blues
____ Fighting Tools
____ The Home Front
____ Rumors

1944:
____ Booby Traps
____ Snafuperman
____ Private Snafu Vs. Malaria Mike
____ A Lecture On Camouflage
____ Gas
____ The Chow Hound
____ Censored
____ Outpost
____ Pay Day
____ Target: Snafu
____ The Three Brothers

1945:
____ In the Aleutians
____ It's Murder She Says
____ Hot Spot
____ Operation: Snafu
____ No Buddy Atoll

Unreleased:
____ Coming Home
____ Secrets of the Caribbean

----------------------------------------

HOOK SHORTS (MADE FOR THE U.S. NAVY):

1945:
____ The Return of Mr. Hook
____ The Good Egg
____ Tokyo Woes

----------------------------------------

MOVIES [STARRING THE LOONEY TUNES CHARACTERS]:

1975:
____ Bugs Bunny Superstar

1979:
____ The Bugs Bunny/Road Runner Movie

1981:
____ Friz Freleng's Looney Looney Looney Bugs Bunny Movie

1982:
____ Bugs Bunny's 3rd Movie: 1001 Rabbit Tales

1983:
____ Daffy Duck's Movie: Fantastic Island

1988:
____ Daffy Duck's Quackbusters

1996:
____ Space Jam

2000:
____ Tweety's High-Flying Adventure (direct-to-video)

2003:
____ Looney Tunes: Back in Action

2006:
____ Bah Hamduck: A Looney Tunes Christmas

----------------------------------------

TV SPECIALS [STARRING THE LOONEY TUNES CHARACTERS]:

1976:
____ Carnival of the Animals

1977:
____ Bugs Bunny's Easter Special
____ Bugs Bunny in Space

1978:
____ A Connecticut Rabbit in King Arthur's Court
____ Bugs Bunny's Howl-Oween Special
____ How Bugs Bunny Won the West

1979:
____ Bugs Bunny's Valentine
____ The Bugs Bunny Mother's Day Special
____ Bugs Bunny's Thanksgiving Diet
____ Bugs Bunny's Looney Christmas Tales

1980:
____ Daffy Duck's Easter Special
____ Bugs Bunny's Busting Out All Over
____ The Bugs Bunny Mystery Special

1981:
____ Bugs Bunny: All American Hero
____ Daffy Duck's Thanks-For-Giving Special

1982:
____ Bugs Bunny's Mad World of Television

1986:
____ Bugs Bunny/Looney Tunes 50th Anniversary Special

1988:
____ Bugs Vs. Daffy: Battle of the Music Video Stars

1989:
____ Bugs Bunny's Wild World of Sports

1990:
____ Happy Birthday Bugs!: 50 Looney Years

1991:
____ Bugs Bunny's Overtures to Disaster

1992:
____ Bugs Bunny's Creature Features
____ Bugs Bunny's Lunar Tunes (released straight to video)
"""

OUT_DIR = os.path.join(os.path.dirname(__file__), '._state', 'tv_episode_cache')
OUT_PATH = os.path.join(OUT_DIR, 'looney_tunes_full_filmography.json')

os.makedirs(OUT_DIR, exist_ok=True)

print("Parsing archived Looney Tunes Cartoon Checklist...")

entries = []
current_year = None
global_index = 0

lines = CHECKLIST_TEXT.split('\n')
for line in lines:
    line = line.strip()
    if not line:
        continue

    # Year headers
    year_match = re.match(r'^(\d{4}):$', line)
    if year_match:
        current_year = year_match.group(1)
        continue

    # Skip section headers
    if line.startswith('MISC.') or line.startswith('PRIVATE SNAFU') or line.startswith('HOOK') or line.startswith('MOVIES') or line.startswith('TV SPECIALS') or line.startswith('----------------------------------------'):
        current_year = None
        continue

    # Title lines (start with ____)
    if line.startswith('____'):
        title = line[4:].strip()  # Remove ____ prefix
        if title and current_year:
            global_index += 1
            entries.append({
                'global_index': global_index,
                'title': title,
                'year': current_year,
                'date': None,  # No specific dates in this checklist
                'source': 'Looney Tunes Cartoon Checklist (archived)'
            })

print(f"Parsed {len(entries)} entries; writing {OUT_PATH}...")
with open(OUT_PATH, 'w', encoding='utf-8') as f:
    json.dump({
        'count': len(entries),
        'source': 'Looney Tunes Cartoon Checklist (archived)',
        'entries': entries
    }, f, indent=2, ensure_ascii=False)

print('Done.')
print(f"First 5 entries: {entries[:5]}")
print(f"Last 5 entries: {entries[-5:]}")