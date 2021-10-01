.PHONY: start
start:
	docker-compose up --build -d

.PHONY: stop
stop:
	docker-compose down -v

.PHONY: restart
restart:
	docker-compose restart

.PHONY: clean
clean:
	rm -rf server/data/*

.PHONY: reset
reset: stop clean

.PHONY: logs
logs:
	docker-compose logs -f
