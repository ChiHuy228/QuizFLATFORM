from django import forms


class WordUploadForm(forms.Form):
    title = forms.CharField(
        max_length=200,
        label='',
        widget=forms.TextInput(
            attrs={
                'placeholder': 'Tên bài trắc nghiệm',
                'class': 'form-control',
            }
        )
    )

    docx_file = forms.FileField(
        label='File Word (.docx)'
    )

    def clean_docx_file(self):
        f = self.cleaned_data['docx_file']

        if not f.name.lower().endswith('.docx'):
            raise forms.ValidationError('Chỉ chấp nhận file .docx')

        if f.size > 10 * 1024 * 1024:
            raise forms.ValidationError('File tối đa 10 MB.')

        return f