# KGG Source Chunk 064

- Source: `kgg-update/index.html`
- Lines: 26881-26895

```html
      var editor=document.querySelector("#editorModal .editorSheet");
      return {
        patchId:PATCH_ID,
        menuAnchored:!!(menu&&menu.closest("#createPanel .planHeader")),
        editorDisplay:editor?getComputedStyle(editor).display:"",
        editorColumns:editor?getComputedStyle(editor).gridTemplateColumns:""
      };
    }
  };
})();
</script>
<!-- KGG PATCH END kgg-v053-ui-tablet-stability -->

</body>
</html>
```
