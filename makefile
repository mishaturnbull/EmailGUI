.PHONY :

compiler = pyinstaller
target = src/coordinator.py

ver_major = 2
ver_minor = 0
ver_patch = 0

cflags = -F -y --specpath build --clean --log-level DEBUG

basename = EmailGUI_v$(ver_major).$(ver_minor).$(ver_patch)

ifeq ($(OS),Windows_NT)
	name = $(basename).exe
	#cflags += --windowed
	delete_cmd = del /S
	delete_dir = rmdir /S /q
	pathsep = ;
else
	UNAME_S = $(shell uname -s)
	ifeq ($(UNAME_S),Darwin)
		name = $(basename)_mac
		#cflags += --windowed
	else
		name = $(basename)_unix
		cflags += -c
	endif
	delete_cmd = rm
	delete_dir = rm -rf
	pathsep = :
endif

datafiles = --add-data "../src/lorem.txt$(pathsep)lorem.txt"
datafiles += --add-data "../src/validation.regex$(pathsep)validation.regex"
datafiles += --add-data "../src/GUI_DOC.template$(pathsep)GUI_Doc.template"
datafiles += --add-data "../src/settings.default.json$(pathsep)settings.default.json"

cflags += $(datafiles) -n $(name)

all: preclean main

clean: preclean postclean

preclean:
	-$(delete_dir) dist
	-$(delete_dir) "src/__pycache__"

postclean:
	-$(delete_dir) build

main:
	$(compiler) $(cflags) $(target)

debug:
	$(compiler) $(cflags) --debug all $(target)

print-% : ; @echo $* = $($*)
