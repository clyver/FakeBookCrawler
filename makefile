webcrawler:
	@echo -e "./webcrawler.py \$$@" > ./webcrawler
	@chmod 700 ./webcrawler
clean:
	@rm ./webcrawler
