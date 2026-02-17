PYPI_REPO := testpypi

all: clean install build wheel test

configure:
	cd gnubg-nn && autoreconf -i &&	./configure

clean:
	rm -rf build/ dist/ analyze/
	rm -rf gnubg/*.egg-info
	rm -rf *.egg-info
	find . -name "*.o" -delete
	find . -name "*.so" -delete
	find . -name "*.a" -delete
	find . -name "config.h" -not -path "./build/*" -delete

install:
	pip install --upgrade pip setuptools wheel cibuildwheel twine meson ninja

build:
	meson setup build
	meson compile -C build

wheel:
	cibuildwheel --platform linux --output-dir dist

twine: twine_linux twine_macos twine_windows
twine_macos:
	twine upload --verbose --repository $(PYPI_REPO) dist/macos/*.whl
twine_linux:
	twine upload --verbose --repository $(PYPI_REPO) dist/linux/*.whl
twine_windows:
	twine upload --verbose --repository $(PYPI_REPO) dist/windows/*.whl

test:
	python3 -m pytest tests/

patch:
	cp -rf patches/gnubg-nn/* gnubg-nn/

# Check-in code after formatting
checkin: ## Perform a check-in after formatting the code
    ifndef COMMIT_MESSAGE
		$(eval COMMIT_MESSAGE := $(shell bash -c 'read -e -p "Commit message: " var; echo $$var'))
    endif
	@git add --all; \
	  git commit -m "$(COMMIT_MESSAGE)"; \
	  git push

install_docs:
	pip install -r requirements.txt ;\

.PHONY: docs
docs:
	$(MAKE) -C docs
