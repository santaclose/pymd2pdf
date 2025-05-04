import re
import os
import sys
import json

from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

moduleFolder = os.path.dirname(__file__)

pdfmetrics.registerFont(TTFont('firaregular', os.path.join(moduleFolder, 'FiraSans', 'FiraSans-Regular.ttf')))
pdfmetrics.registerFont(TTFont('firabold', os.path.join(moduleFolder, 'FiraSans', 'FiraSans-Bold.ttf')))
pdfmetrics.registerFont(TTFont('firacode', os.path.join(moduleFolder, 'FiraCode', 'FiraCode-Regular.ttf')))

with open("config.json", 'r') as configFile:
	CONFIG = json.loads(configFile.read())

PARAGRAPH_STYLE = ParagraphStyle(
	name='Normal',
	fontName='firaregular',
	fontSize=CONFIG['paragraph_font_size'],
)

MULTILINE_CODE_STYLE = ParagraphStyle(
	name='Normal',
	fontName='firacode',
	fontSize=CONFIG['code_font_size'],
)


def generatePdf(inputFileName, outputFileName="out.pdf", pdfTitle=""):

	pdf = canvas.Canvas(outputFileName)
	pdf.setTitle(pdfTitle)
	pdf.setPageSize((CONFIG['page_width'], CONFIG['page_height']))

	COLUMN_SIZE = CONFIG['page_width'] - 2 * CONFIG['x_margin']
	COLUMN_SIZE -= (CONFIG['column_count'] - 1) * CONFIG['column_margin']
	COLUMN_SIZE = COLUMN_SIZE / CONFIG['column_count']

	currentColumn = 0
	cursorX = CONFIG['x_margin']
	cursorY = CONFIG['page_height'] - CONFIG['y_margin']

	with open(inputFileName, 'r') as mdFile:

		multilineCodeMode = False

		for i, line in enumerate(mdFile.read().split('\n')):

			lineSeparation =  CONFIG['line_separation']

			if line == '```':
				multilineCodeMode = not multilineCodeMode;
				continue

			if multilineCodeMode:

				P = Paragraph(line, style=MULTILINE_CODE_STYLE)
				aH = cursorY
				w, h = P.wrap(COLUMN_SIZE, aH)
				if w > COLUMN_SIZE or h > aH:
					print("not enough space for paragraph")
					break;
				cursorY -= h

				textWidth = pdfmetrics.stringWidth(line, MULTILINE_CODE_STYLE.fontName, MULTILINE_CODE_STYLE.fontSize)
				pdf.setStrokeColorRGB(0.9,0.9,0.9)
				pdf.setFillColorRGB(0.9,0.9,0.9)
				pdf.roundRect(cursorX - 5, cursorY - 5, textWidth + 10, h + 5, 3, fill=1, stroke=0)
				P.drawOn(pdf, cursorX, cursorY)

				cursorY -= lineSeparation

				continue


			headerMatch = re.match(r"^(#+) .+", line)
			imageMatch = re.match(r"^!\[\w*\]\(([^\(\)]+)\).*", line)

			if headerMatch is not None:

				if i > 0: # replace line separation with bigger one
					lineSeparation =  CONFIG['header_separation']

				hashtagCount = len(headerMatch.group(1, 0)[0])
				headerFontSize = CONFIG['header_font_size'] - 2 * hashtagCount

				P = Paragraph(line[hashtagCount + 1:], style=ParagraphStyle(
						name='Header',
						fontName='firabold',
						fontSize=headerFontSize,
					)
				)
				aH = cursorY
				w, h = P.wrap(COLUMN_SIZE, aH)
				if w > COLUMN_SIZE or h > aH:
					print("not enough space for paragraph")
					break;
				cursorY -= h
				P.drawOn(pdf, cursorX, cursorY)

			elif imageMatch is not None:

				imagePath = imageMatch.group(0, 1)[1]
				cursorY -= 256
				pdf.drawInlineImage(imagePath, cursorX, cursorY, width=256, height=256)

			else:

				inlineCodeMatch = re.findall(r"(`[^`]+`)", line)
				inlineLinkMatch = re.findall(r"(\[([^]]+)\]\(([^)]+)\))", line)
				processedLine = line
				for item in inlineCodeMatch:
					processedLine = processedLine.replace(item, '<font face="firacode">' + item[1:-1] + '</font>')
				for item in inlineLinkMatch:
					processedLine = processedLine.replace(item[0], f'<font color="green"><link href="{item[2]}">{item[1]}</link></font>')
				isBulletLine = processedLine[:2] == "- "
				if isBulletLine:
					lineSeparation =  CONFIG['bullet_line_separation']
					processedLine = processedLine[2:]
					pdf.setStrokeColorRGB(0,0,0)
					pdf.setFillColorRGB(0,0,0)
					pdf.circle(cursorX, cursorY - 6.5, 1.5, fill=1)

				P = Paragraph(processedLine, style=PARAGRAPH_STYLE)
				aH = cursorY
				w, h = P.wrap(COLUMN_SIZE, aH)
				if w > COLUMN_SIZE or h > aH:
					print("not enough space for paragraph")
					break;
				cursorY -= h
				P.drawOn(pdf, cursorX + (10 if isBulletLine else 0), cursorY)

			cursorY -= lineSeparation

			# jump to next column if needed
			if cursorY < CONFIG['y_margin'] and currentColumn < CONFIG['column_count'] - 1:
				cursorX += COLUMN_SIZE + CONFIG['column_margin']
				cursorY = CONFIG['page_height'] - CONFIG['y_margin']
				currentColumn += 1

	pdf.save()

if __name__ == "__main__":
	if len(sys.argv) < 2:
		print("Usage: md2pdf <inputMdFile>")
		sys.exit(1)
	generatePdf(sys.argv[1])