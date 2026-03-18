/* BioScale — Export page to PNG using html2canvas */

let h2cLoaded = false;

function loadH2C() {
    if (h2cLoaded) return Promise.resolve();
    return new Promise(function(resolve, reject) {
        var s = document.createElement('script');
        s.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
        s.onload = function() { h2cLoaded = true; resolve(); };
        s.onerror = function() { reject(new Error('Failed to load html2canvas')); };
        document.head.appendChild(s);
    });
}

document.addEventListener('click', async function(e) {
    var btn = e.target.closest('.btn-export');
    if (!btn) return;

    var icon = btn.querySelector('.export-icon');
    var spinner = btn.querySelector('.export-spinner');

    btn.disabled = true;
    if (icon) icon.style.display = 'none';
    if (spinner) spinner.style.display = 'block';

    try {
        await loadH2C();

        var target = document.getElementById('page-content');
        if (!target) {
            alert('Conteúdo não encontrado.');
            return;
        }

        var canvas = await html2canvas(target, {
            backgroundColor: '#F5F7FA',
            scale: 2,
            useCORS: true,
            logging: false,
            windowWidth: 480,
        });

        var link = document.createElement('a');
        var filename = btn.getAttribute('data-filename') || 'bioscale';
        var now = new Date();
        var dateStr = now.getFullYear() + '-' +
            String(now.getMonth() + 1).padStart(2, '0') + '-' +
            String(now.getDate()).padStart(2, '0');
        link.download = filename + '_' + dateStr + '.png';
        link.href = canvas.toDataURL('image/png');
        link.click();
    } catch (err) {
        console.error('Export error:', err);
        alert('Erro ao exportar: ' + err.message);
    } finally {
        btn.disabled = false;
        if (icon) icon.style.display = 'block';
        if (spinner) spinner.style.display = 'none';
    }
});
