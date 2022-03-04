import re

from reportlab.platypus import Paragraph
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfgen import canvas
from reportlab.rl_config import defaultPageSize
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics

pdfmetrics.registerFont(TTFont('firaregular', 'FiraSans/FiraSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('firabold', 'FiraSans/FiraSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('firacode', 'FiraCode/FiraCode-Regular.ttf'))

PAGE_WIDTH = defaultPageSize[0]
PAGE_HEIGHT = defaultPageSize[1]

TOP_MARGIN = 50
LEFT_MARGIN = 45
RIGHT_MARGIN = 45

LINE_SEPARATION = 8
HEADER_SEPARATION = 36

PARAGRAPH_STYLE = ParagraphStyle(
	name='Normal',
	fontName='firaregular',
	fontSize=11,
)

MULTILINE_CODE_STYLE = ParagraphStyle(
	name='Normal',
	fontName='firacode',
	fontSize=13,
)


def generatePdf(inputFileName, outputFileName="out.pdf", pdfTitle=""):

	pdf = canvas.Canvas(outputFileName)
	pdf.setTitle(pdfTitle)
	pdf.setPageSize((PAGE_WIDTH, PAGE_HEIGHT))

	cursorX = LEFT_MARGIN
	cursorY = PAGE_HEIGHT - TOP_MARGIN

	with open(inputFileName, 'r') as mdFile:

		multilineCodeMode = False

		for i, line in enumerate(mdFile.read().split('\n')):

			if line == '```':
				multilineCodeMode = not multilineCodeMode;
				continue

			if multilineCodeMode:

				P = Paragraph(line, style=MULTILINE_CODE_STYLE)
				aW = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
				aH = cursorY
				w, h = P.wrap(aW, aH)
				if w > aW or h > aH:
					print("not enough space for paragraph")
					break;
				cursorY -= h

				textWidth = pdfmetrics.stringWidth(line, MULTILINE_CODE_STYLE.fontName, MULTILINE_CODE_STYLE.fontSize)
				pdf.setStrokeColorRGB(0.9,0.9,0.9)
				pdf.setFillColorRGB(0.9,0.9,0.9)
				pdf.roundRect(cursorX - 5, cursorY - 5, textWidth + 10, h + 5, 3, fill=1, stroke=0)
				P.drawOn(pdf, cursorX, cursorY)

				cursorY -= LINE_SEPARATION

				continue


			headerMatch = re.match(r"^(#+) .+", line)
			imageMatch = re.match(r"^!\[\w*\]\(([^\(\)]+)\).*", line)

			if headerMatch is not None:

				if i > 0: # replace line separation with bigger one
					cursorY += LINE_SEPARATION
					cursorY -= HEADER_SEPARATION

				hashtagCount = len(headerMatch.group(1, 0)[0])
				headerFontSize = (7 - hashtagCount) * 2 + 8

				P = Paragraph(line[hashtagCount + 1:], style=ParagraphStyle(
						name='Header',
						fontName='firabold',
						fontSize=headerFontSize,
					)
				)
				aW = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
				aH = cursorY
				w, h = P.wrap(aW, aH)
				if w > aW or h > aH:
					print("not enough space for paragraph")
					break;
				cursorY -= h
				P.drawOn(pdf, cursorX, cursorY)

				cursorY -= LINE_SEPARATION * 2 # more separation for headers

			elif imageMatch is not None:

				imagePath = imageMatch.group(0, 1)[1]
				cursorY -= 256
				pdf.drawInlineImage(imagePath, cursorX, cursorY, width=256, height=256)

				cursorY -= LINE_SEPARATION

			else:

				m = re.findall(r"(`[^`]+`)", line)
				processedLine = line
				for item in m:
					processedLine = processedLine.replace(item, '<font face="firacode">' + item[1:-1] + '</font>')
				isBulletLine = processedLine[:2] == "- "
				if isBulletLine:
					processedLine = processedLine[2:]
					pdf.setStrokeColorRGB(0,0,0)
					pdf.setFillColorRGB(0,0,0)
					pdf.circle(cursorX, cursorY - 7, 1.5, fill=1)

				P = Paragraph(processedLine, style=PARAGRAPH_STYLE)
				aW = PAGE_WIDTH - LEFT_MARGIN - RIGHT_MARGIN
				aH = cursorY
				w, h = P.wrap(aW, aH)
				if w > aW or h > aH:
					print("not enough space for paragraph")
					break;
				cursorY -= h
				P.drawOn(pdf, cursorX + (10 if isBulletLine else 0), cursorY)

				cursorY -= LINE_SEPARATION

	pdf.save()