/* CartABl - interactive SVG runtime */

/*
  CartABl - declarative interaction layer for SVG
  Copyright (C) 2022 Olivier Aubert

  This program is free software; you can redistribute it and/or
  modify it under the terms of the GNU Lesser General Public License
  as published by the Free Software Foundation; either version 2.1
  of the License, or (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU Lesser General Public License for more details.

  You should have received a copy of the Lesser GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

/*
 * It is meant to be added to an existing SVG file and expects to
 * find interaction definitions stored as <svgaction> elements as
 * <metadata> children.
 */

/* ACTIONS/EVENTS definition will be extracted into interactions.js

   In order to able to
   import { EVENTS, ACTIONS } from "./interactions.js"
   (in the editor), the
   export { ACTIONS, EVENTS }
   line will be added after extraction.

   Node: modules are not supported in XML docs (hence SVG)
   (https://bugs.chromium.org/p/chromium/issues/detail?id=717643)
*/

/* Note: the code between the start of/end of markers below is
 * extracted into the interactions.js module, and an export clause is
 * appended, by the scripts/extract_actions
 * so that we obtain a js module that can be imported in the editor.
 */

/* START_OF_INTERACTIONS */
/*
  CartABl - declarative interaction layer for SVG
  Copyright (C) 2022 Olivier Aubert

  This program is free software: you can redistribute it and/or modify
  it under the terms of the GNU General Public License as published by
  the Free Software Foundation, either version 3 of the License, or
  (at your option) any later version.

  This program is distributed in the hope that it will be useful,
  but WITHOUT ANY WARRANTY; without even the implied warranty of
  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
  GNU General Public License for more details.

  You should have received a copy of the GNU General Public License
  along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

/* Helper function for actions */
function getTargets(source, selector = null) {
    /* General behaviour: given a source (DOM element) and a CSS selector,
       return a list of elements matching selector.
       If selector is null then a list with the single item source is returned.
    */
    let elements = [ source ];
    if (selector == 'document') {
        elements = [ document ]
    } else if (selector == 'this') {
        elements = [ source ]
    } else if (selector !== null) {
        elements = [ ...document.querySelectorAll(selector) ];
    }
    return elements;
}

/* Apply an action to elements specified through CSS selectors, in the context of a *source* DOM element

   The most basic case is to have a selector that references a single element (like #id). In this case, the function
is simply called with the element as parameter.

   If the selector is not specified (or the special string "this"), then  the *source* element will be used as default parameter.

 */
function applyAction(source, selector, func) {
    let elements = getTargets(source, selector);
    elements.forEach(func);
    return elements;
}

/*!
 * Get an object value from a specific path
 * (c) 2018 Chris Ferdinandi, MIT License, https://gomakethings.com
 * @param  {Object}       obj  The object
 * @param  {String|Array} path The path
 * @param  {*}            def  A default value to return [optional]
 * @return {*}                 The value
 */
var get = function (obj, path, def) {
	/**
	 * If the path is a string, convert it to an array
	 * @param  {String|Array} path The path
	 * @return {Array}             The path array
	 */
	var stringToPath = function (path) {

		// If the path isn't a string, return it
		if (typeof path !== 'string') return path;

		// Create new array
		var output = [];

		// Split to an array with dot notation
		path.split('.').forEach(function (item) {

			// Split to an array with bracket notation
			item.split(/\[([^}]+)\]/g).forEach(function (key) {

				// Push to the new array
				if (key.length > 0) {
					output.push(key);
				}

			});

		});

		return output;

	};

	// Get the path as an array
	path = stringToPath(path);

	// Cache the current object
	var current = obj;

	// For each item in the path, dig into the object
	for (var i = 0; i < path.length; i++) {

		// If the item isn't found, return the default (or null)
		if (!current[path[i]]) return def;

		// Otherwise, update the current  value
		current = current[path[i]];

	}

	return current;

};

/*!
 * Replaces placeholders with real content
 * Requires get() - https://vanillajstoolkit.com/helpers/get/
 * (c) 2019 Chris Ferdinandi, MIT License, https://gomakethings.com
 * @param {String} template The template string
 * @param {String} local    A local placeholder to use, if any
 */
var placeholders = function (template, data) {

	'use strict';

	// Check if the template is a string or a function
	template = typeof (template) === 'function' ? template() : template;
	if (['string', 'number'].indexOf(typeof template) === -1) throw 'PlaceholdersJS: please provide a valid template';

	// If no data, return template as-is
	if (!data) return template;

	// Replace our curly braces with data
	template = template.replace(/\{\{([^}]+)\}\}/g, function (match) {

		// Remove the wrapping curly braces
		match = match.slice(2, -2);

		// Get the value
		var val = get(data, match.trim());

		// Replace
		if (!val) return '{{' + match + '}}';
		return val;

	});

	return template;

};

const ACTIONS = {
    addClass: {
        label: "ajouter la classe {classname} à {selector}",
        action: (source, { selector, classname }) => {
            applyAction(source, selector,
                        e => { e.classList.add(classname) });
        },
    },
    removeClass: {
        label: "supprimer la classe {classname} de {selector}",
        action: (source, { selector, classname }) => {
            applyAction(source, selector,
                        e => { e.classList.remove(classname) });
        },
    },
    toggleClass: {
        label: "inverser la classe {classname} de {selector}",
        action: (source, { selector, classname }) => {
            applyAction(source, selector,
                        e => { e.classList.toggle(classname); });
        },
    },
    /* Generic visibility manipulation show/hide/toggle */
    show: {
        label: "afficher {selector}",
        action: (source, { selector = null }) => {
            applyAction(source, selector,
                        e => { e.style.display = 'block';
                               /* Make sure children are visible too */
                               e.querySelectorAll("*").forEach(child => child.style.display = 'block')
                             });
        },
    },
    hide: {
        label: "cacher {selector}",
        action: (source, { selector = null }) => {
            applyAction(source, selector,
                        e => { e.style.display = 'none'; });
        },
    },
    show_only: {
        label: "afficher seulement {selector}",
        action: (source, { selector = null }) => {
            applyAction(source, selector,
                e => {
                    // Hide all children of the parent
                    e.parentElement.querySelectorAll("*").forEach(child => child.style.display = 'none');
                    // Show only the selected element
                    e.style.display = 'block';
                    /* Make sure its children are visible too */
                    e.querySelectorAll("*").forEach(child => child.style.display = 'block');
                });
        },
    },
    toggle: {
        label: "inverser la visibilité de {selector}",
        action: (source, { selector = null }) => {
            applyAction(source, selector,
                        e => {
                            if (e.style.display == 'none') {
                                e.style.display = 'block';
                            } else {
                                e.style.display = 'none';
                            }
                        });
        },
    },
    set_opacity: {
        label: "fixer l'opacité de {selector} à {opacity}",
        action: (source, { selector, opacity }) => {
            let value = parseFloat(opacity);
            if (! isNaN(value))
                applyAction(source, selector,
                            e => { e.style.opacity = value; });
        },
    },
    send_event: {
        label: "émettre un événement {event_name}",
        action: (source, { event_name }) => {
            document.dispatchEvent(new CustomEvent(event_name, { detail: { source }, bubble: true, composed: true }));
        },
    },

    panzoom: {
        label: "zoomer sur {selector}",
        action: (source, { selector }) => {
            let action_representation = `panzoom(${selector})`;

            if (selector != 'this' && selector != '') {
                // Zoom rectangle
                let ref = document.querySelector(selector);
                // Owner SVG element
                let svg = ref.ownerSVGElement;
                let action = svg.dataset._action;
                if (action == action_representation) {
                    // Same action - revert it
                    svg.style.transform = '';
                    svg.dataset._action = undefined;
                    return;
                }
                /* getBoundingClientRect returns a DOMRect, in screen units */
                let box = ref.getBoundingClientRect();
                let whole = svg.getBoundingClientRect();
                let box_middle = { x: box.x + box.width / 2,
                                   y: box.y + box.height / 2 };
                let whole_middle = { x: whole.x + whole.width / 2,
                                     y: whole.y + whole.height / 2 };

                /* See https://stackoverflow.com/questions/16359246/how-to-extract-position-rotation-and-scale-from-matrix-svg */
                let m = ref.getScreenCTM();
                let angle = Math.round(Math.atan2(m.b, m.a) * (180/Math.PI));
                let scalex = Math.sqrt(m.a * m.a + m.b * m.b);
                let scaley = Math.sqrt(m.c * m.c + m.d * m.d);
                /*
                  This is in SVG units - we do not need them here since we use CSS transforms:
                let translatex = m.e;
                let translatey = m.f;
                // old experiment - keep for possible reference
                // Note: Here we are  using SVG transform (no px unit, no transform-origin)
                let svg_transform = `rotate(${-angle}, ${box_middle.x}, ${box_middle.y})`;
                // scale(${scale}) translate(${whole_middle.x}, ${whole_middle.y})`);
                // svg.setAttribute("transform", svg_transform);
                */

                // For scaling we get the reference width/height of the zoom
                // rectangle itself (possibly rotated), and if not a rectangle of the shape bounding box.
                // Use it to compute a global scale ratio.
                let refwidth = ref.getBBox().width;
                let refheight = ref.getBBox().height;
                if (ref.tagName == 'rect') {
                    refwidth = ref.width.baseVal.value;
                    refheight = ref.height.baseVal.value;
                }
                let scale = Math.min((whole.width / scalex)  / refwidth, (whole.height / scaley) / refheight);

                // Note: this is a CSS transform:
                // We will center figure first, then apply transforms
                svg.style.transformOrigin = "center center";
                // !! transform functions are multiplied from left to
                // right, which means that tranforms are applied from
                // right to left (i.e. translate first here)
                let css_transform = `scale(${scale}) rotate(${-angle}deg) translate(${Math.round(whole_middle.x - box_middle.x)}px, ${Math.round(whole_middle.y - box_middle.y)}px)`;
                svg.style.transition = "transform 1000ms ease-in-out";
                svg.style.overflow = "hidden";
                svg.style.transform = css_transform;
                svg.dataset._action = action_representation;
                // console.log({ ref, svg, box, box_middle, whole, whole_middle, m, scale });
                // console.log({ css_transform });
            }
        }
    },
    show_template: {
        label: "afficher le modèle {selector}",
        action: (source, { selector }) => {
            applyAction(source, selector,
                        e => {
                            // Replace template placeholders
                            if (e.dataset._original_content === undefined) {
                                e.dataset._original_content = e.innerHTML;
                            }
                            e.innerHTML = placeholders(e.dataset._original_content, {
                                origin: source,
                                element: e
                            });
                            // Display the element
                            e.style.display = 'block';
                            // Make sure children are visible too
                            e.querySelectorAll("*").forEach(child => child.style.display = 'block')
                        });
        }
    }
};

const EVENTS = {
    "click": {
        label: "clique sur",
        parameters: [ "source" ]
    },
    "mouseover": {
        label: "survole",
        parameters: [ "source" ]
    },
    "mouseenter": {
        label: "entre dans",
        parameters: [ "source" ]
    },
    "mouseleave": {
        label: "quitte",
        parameters: [ "source" ]
    },
    "custom": {
        label: "reçoit l’événement",
        parameters: [ "event_name" ]
    },
    "document-load": {
        label: "ouvre le document",
        parameters: []
    }
};
/* END_OF_INTERACTIONS */

function message(...p) {
    console.log(...p);
    document.dispatchEvent(new CustomEvent("message", { detail: { message: p }, bubble: true, composed: true }));
}

function default_action(source, params) {
    message("DEFAULT ACTION", source, params);
}

// Link actions to elements through <metadata> elements
function init_cartabl () {
    document.querySelectorAll("metadata rule").forEach(node => {
        // Convert NamedNodeMap to more convenient object
        let rule = Object.fromEntries(node.getAttributeNames().map(n => [n, node.getAttribute(n)]));

        let sources = [];
        if (EVENTS[rule.event] && EVENTS[rule.event].parameters.length > 0) {
            sources = document.querySelectorAll(rule.source);
            if (sources.length == 0) {
                message(`Cannot find any source matching ${rule.source} for ${rule.event}`);
            }
        }
        // Convert action DOM nodes to objects
        let actions = [ ...node.querySelectorAll("action")].map(actionnode => {
            let attrs = Object.fromEntries([ ...actionnode.attributes ].map(a => [ a.name, a.value ]));
            // Lookup ACTIONS
            attrs.action = ACTIONS[attrs.name].action || default_action;
            return attrs;
        });
        rule.actions = actions;

        // FIXME: check validity of event
        // FIXME: implement synthetic "hover" event, which triggers a "start" action on mouseover and a "end" action on mouseout.
        sources.forEach(source => {
            // Update cursor
            source.style.cursor = 'pointer';
            // Pass the whole "att" object so that any parameters are correctly passed.
            source.addEventListener(rule.event, () => {
                // Dispatch event (so that it can be handled by embedding containers if so needed.
                document.dispatchEvent(new CustomEvent("svgaction", { detail: rule, bubble: true, composed: true }));
                rule.actions.forEach(action => action.action(source, action));
            });
        });
        // Process parameterless events (document-load for now)
        if (rule.event == 'document-load') {
            // Trigger actions
            source = document;
            // Dispatch event (so that it can be handled by embedding containers if so needed.
            document.dispatchEvent(new CustomEvent("svgaction", { detail: rule, bubble: true, composed: true }));
            rule.actions.forEach(action => action.action(source, action));
        } else if (rule.event == 'custom') {
            // Handling of custom events.
            source = document;
            document.addEventListener(rule.event_name, () => {
                rule.actions.forEach(action => action.action(source, action))
            })
        }
    });
}

/* Hook interactive behaviour. We assume for the moment that this
   script is injected at the end of the SVG file, so that we know the
   DOM (esp. the <metadata> node) is loaded.

   For more robustness, we could either use DOMContentLoaded or emulate jquery.ready()
*/
init_cartabl();
message("Initialized CartABl");
