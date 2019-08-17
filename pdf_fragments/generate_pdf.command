#! /bin/bash

cd '/Users/Ben/Desktop/COSC 264/Socket Assignment/'



#(echo ":syntax on"; echo ":hardcopy > pdf_fragments/postscript/server.ps") | vim server.py
#(echo ":syntax on"; echo ":hardcopy > pdf_fragments/postscript/client.ps") | vim client.py
#(echo ":syntax on"; echo ":hardcopy > pdf_fragments/postscript/records.ps") | vim records.py
#(echo ":syntax on"; echo ":hardcopy > pdf_fragments/postscript/common.ps") | vim common.py

vim +'syntax on | hardcopy > pdf_fragments/postscript/server.ps | q!' server.py
vim +'syntax on | hardcopy > pdf_fragments/postscript/client.ps | q!' client.py
vim +'syntax on | hardcopy > pdf_fragments/postscript/packet.ps | q!' packet.py
vim +'syntax on | hardcopy > pdf_fragments/postscript/records.ps | q!' records.py
vim +'syntax on | hardcopy > pdf_fragments/postscript/common.ps | q!' common.py


cd ./pdf_fragments

ps2pdf ./postscript/server.ps
ps2pdf ./postscript/client.ps
ps2pdf ./postscript/packet.ps
ps2pdf ./postscript/records.ps
ps2pdf ./postscript/common.ps

pdftk coversheet.pdf server.pdf client.pdf common.pdf packet.pdf records.pdf plagiarism_declaration.pdf cat output ../final.pdf
