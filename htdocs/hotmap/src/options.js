/**
 * options.js
 *
 * Panel for various options.
 *
 * Authors: nconrad
 *
 */
export default class Options {

    constructor(args) {
        this.openBtn = args.openBtn;
        this.onSortChange = args.onSortChange;
        this.onColorChange = args.onColorChange;
        this.onSnapshot = args.onSnapshot;
        this.onFullSnapshot = args.onFullSnapshot;

        //this._altColors = args.altColors;
        this._color = args.color;
        this._viewerNode = this.openBtn.parentNode.parentNode;
        this._show = false;

        this.init();
    }

    init() {
        let ele = this._viewerNode;

        let optsBtn = this.openBtn;
        optsBtn.onclick = (evt) => {
            this._show = !this._show;
            if (this._show) {
                this.show(evt);
            } else {
                this.hide();
                return;
            }

            let close = (evt) => {
                if (ele.querySelector('.options').contains(evt.target)) return;
                this.hide();
                ele.removeEventListener('click', close);
                this._show = false;
            };
            ele.addEventListener('click', close);
        };

        ele.querySelector('.close-btn').onclick = () => this.hide();

        /*
        if (this._altColors) {
            let el = ele.querySelector('.colors');
            el.classList.remove('hidden');
            el.onclick = () => this._onColor;
        }*/
        // this.colorEventInit();

        let snapshotBtn = ele.querySelector('.download [data-id="snapshot"]');
        snapshotBtn.onclick = () => {
            let progress = ele.querySelector('.download-progress');
            progress.innerHTML = 'Creating SVG...';
            setTimeout(() => {
                this.onSnapshot();
                progress.innerHTML = '';
            }, 100);
        };

        let fullSnapshotBtn = ele.querySelector('.download [data-id="full-chart"]');
        fullSnapshotBtn.onclick = () => {
            let progress = ele.querySelector('.download-progress');
            progress.innerHTML = 'Creating SVG... This may take awhile for large charts.';
            setTimeout(() => {
                this.onFullSnapshot();
                progress.innerHTML = '';
            }, 100);
        };
    }

    show(evt) {
        evt.stopPropagation();
        this._viewerNode.querySelector('.options').style.visibility = 'visible';
        this._viewerNode.querySelector('.options').style.height = `${200 - 4}px`;
    }

    hide() {
        this._viewerNode.querySelector('.options').style.height = '0';
        setTimeout(() => {
            this._viewerNode.querySelector('.options').style.visibility = 'hidden';
        });
    }

    // not currently used
    sortEventInit() {
        let sortNodes = this._viewerNode.querySelectorAll('.options .sorting a');
        sortNodes.forEach(node => {
            node.onclick = evt => {
                let ele = evt.target;

                sortNodes.forEach(node => node.classList.remove('active'));

                let type = ele.getAttribute('data-id');
                ele.classList.add('active');
                this.onSort(type);
            };
        });
    }

    colorEventInit() {
        let nodes = this._viewerNode.querySelectorAll('.options .colors a');
        nodes.forEach(node => {
            node.onclick = evt => {
                let ele = evt.target;

                nodes.forEach(node => node.classList.remove('active'));

                let type = ele.getAttribute('data-id');
                ele.classList.add('active');
                this.onColorChange(type);
            };
        });
    }
}


