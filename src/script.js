/**
 * PastMysteries - Site Scripts
 */

(function() {
    'use strict';

    // Netflix-style carousel scrolling
    document.querySelectorAll('.carousel-wrapper').forEach(function(wrapper) {
        var track = wrapper.querySelector('.carousel-track');
        var btnLeft = wrapper.querySelector('.carousel-btn-left');
        var btnRight = wrapper.querySelector('.carousel-btn-right');

        if (!track) return;

        var scrollAmount = 280; // card width + gap

        function updateButtons() {
            if (!btnLeft || !btnRight) return;
            // Hide left button if at start
            if (track.scrollLeft <= 10) {
                btnLeft.style.opacity = '0';
                btnLeft.style.pointerEvents = 'none';
            } else {
                btnLeft.style.opacity = '1';
                btnLeft.style.pointerEvents = 'auto';
            }
            // Hide right button if at end
            var maxScroll = track.scrollWidth - track.clientWidth;
            if (track.scrollLeft >= maxScroll - 10) {
                btnRight.style.opacity = '0';
                btnRight.style.pointerEvents = 'none';
            } else {
                btnRight.style.opacity = '1';
                btnRight.style.pointerEvents = 'auto';
            }
        }

        if (btnRight) {
            btnRight.addEventListener('click', function() {
                track.scrollBy({ left: scrollAmount, behavior: 'smooth' });
            });
        }

        if (btnLeft) {
            btnLeft.addEventListener('click', function() {
                track.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
            });
        }

        track.addEventListener('scroll', updateButtons);
        updateButtons();

        // Keyboard navigation when track is focused
        track.setAttribute('tabindex', '0');
        track.addEventListener('keydown', function(e) {
            if (e.key === 'ArrowRight') {
                track.scrollBy({ left: scrollAmount, behavior: 'smooth' });
            } else if (e.key === 'ArrowLeft') {
                track.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
            }
        });
    });

})();
