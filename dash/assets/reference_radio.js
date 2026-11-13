// Radio button of the "Reference" column of the metadata table (reference genome for projection).
// Same principle as group_checkbox.js: native listeners stop the click so that the row selection
// (rowMultiSelectWithClick) is not toggled. Only the clicked row is set to true: Dash then
// unticks the other rows (callback choose_reference_genome).
var dagcomponentfuncs = (window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {});

dagcomponentfuncs.ReferenceRadio = function (props) {
    const node = props.node;
    const colId = props.column.getColId();
    const ref = React.useRef(null);
    const [selected, setSelected] = React.useState(node.isSelected());

    React.useEffect(() => {
        const onSel = () => setSelected(node.isSelected());
        node.addEventListener('rowSelected', onSel);
        return () => node.removeEventListener('rowSelected', onSel);
    }, [node]);

    React.useEffect(() => {
        const el = ref.current;
        if (!el) { return; }
        const stop = (e) => { e.stopPropagation(); };
        const onClick = (e) => {
            e.stopPropagation();
            if (!node.isSelected() || props.value) { e.preventDefault(); return; }
            node.setDataValue(colId, true);   // -> cellValueChanged sent to Dash
        };
        el.addEventListener('mousedown', stop);
        el.addEventListener('dblclick', stop);
        el.addEventListener('click', onClick);
        return () => {
            el.removeEventListener('mousedown', stop);
            el.removeEventListener('dblclick', stop);
            el.removeEventListener('click', onClick);
        };
    }, [node, colId, props.value]);

    return React.createElement('input', {
        ref: ref,
        type: 'radio',
        checked: !!props.value,
        onChange: () => {},
        disabled: !selected,
        title: selected ? 'Use this genome as reference for the projections'
                        : 'Select the genome first (checkbox of the first column)',
        style: { cursor: selected ? 'pointer' : 'not-allowed', width: '16px', height: '16px' },
    });
};
