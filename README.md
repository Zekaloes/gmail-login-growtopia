How to Use:
1.Download both the folder and gmail.exe.

2.Move both the folder and gmail.exe to your Lucifer folder.

3.Open Lucifer, go to settings, and check 'Use WebDriver'.

Now, when you add a Gmail bot, it will automatically open a browser and log in to your email. 
--------------------------
--------------------------
How to Make It Support G Suite Email (myemail@domain.com):

1.Create a text file named email.txt and import all your emails|passwords in the format shown in the image below.

2.When you add a Lucifer bot, make sure to change the @domain to @gmail. For example, change myname@dighc.com to myname@gmail.com (DO NOT change the one in email.txt).

Done! The setup is complete.
Not Trusting gmail.exe?
You can decompile gmail.exe if u have some coding experiences; it’s not even obfuscated. or you can buy the source code for gmail.exe. 
---------------------
---------------------
[WARNING] 
Dont use any lucifer feature that make it open explorer.exe ( the built in file manager in windows )
It Will Make gmail.exe won't work ( LUCIFER ISSUE ), i tried to report to nuron about this, no response

Example of lucifer feature that open explorer.exe :
load or save current lucifer config
import / export proxy from txt 
import / export farms from txt 
---------------------
---------------------
If U need script to load bulk farm, u can use this script, [ OPEN SOURCE ]
local rotation = getBot().rotation
local file, err = io.open('farms.txt', "r")
world_manager = getWorldManager()


if file then 
    for line in file:lines() do
        world_manager:addFarm(line)
    end
end

make sure u have txt file named farms in ur lucifer folder, with format farm:ids:blockids 
--------------
or if u need any other script that need to added in bulk like adding bunch proxies, bunch of plant world. u can dm me, ill make it for free [ OPEN SOURCE ] 
