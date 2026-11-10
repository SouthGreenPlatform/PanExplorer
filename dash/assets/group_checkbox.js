// Checkbox of the "Compared group" column of the metadata table.
// AG Grid toggles the row selection with a native listener placed on an ancestor of the cell
// (rowMultiSelectWithClick), which runs before React's synthetic events: the click is therefore
// stopped with NATIVE listeners on the input itself, and the value is changed from there.
// Enabled only when the genome (row) is selected.
var dagcomponentfuncs = (window.dashAgGridComponentFunctions = window.dashAgGridComponentFunctions || {});

dagcomponentfuncs.GroupCheckbox = function (props) {
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
            if (!node.isSelected()) { e.preventDefault(); return; }
            // triggers cellValueChanged (sent to Dash) and updates rowData
            node.setDataValue(colId, el.checked);
        };
        el.addEventListener('mousedown', stop);
        el.addEventListener('dblclick', stop);
        el.addEventListener('click', onClick);
        return () => {
            el.removeEventListener('mousedown', stop);
            el.removeEventListener('dblclick', stop);
            el.removeEventListener('click', onClick);
        };
    }, [node, colId]);

    return React.createElement('input', {
        ref: ref,
        type: 'checkbox',
        checked: !!props.value,
        onChange: () => {},
        disabled: !selected,
        title: selected ? 'Add / remove this genome from the compared group'
                        : 'Select the genome first (checkbox of the first column)',
        style: { cursor: selected ? 'pointer' : 'not-allowed', width: '16px', height: '16px' },
    });
};
