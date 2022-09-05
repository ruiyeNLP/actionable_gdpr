from somajo import SoMaJo

tokenizer = SoMaJo("en_PTB", split_sentences=False)

# def detokenize(tokens):
#     out = []
#     for token in tokens:
#         if token.original_spelling is not None:
#             out.append(token.original_spelling)
#         else:
#             out.append(token.text)
#         if token.space_after:
#             out.append(" ")
#     return "".join(out)


def somajo_remove_url(text):
    """
    A customized function to remove e-mails which have whitespaces
    and URLs which were apparently not cleaned from the corpus.
    """
    out = []
    text_as_list = list()
    text_as_list.append(text)
    tokenized_text = tokenizer.tokenize_text(text_as_list)
    for dummy_tokenized_text in tokenized_text:
        # return([detokenize(bla) for bla in tokenized_text][0])
        for token in dummy_tokenized_text:
            if token.token_class == "URL":
                out.append("-URL-")
            elif token.original_spelling is not None:
                out.append(token.original_spelling)
            else:
                out.append(token.text)
            if token.space_after:
                out.append(" ")
    return "".join(out)


list_of_texts = ["For more information on which authority to contact , please email us here support @ infinitygames.io .",
              "For further clarification of the terms used in this Policy please visit our Privacy Center on spotify.com",
              "If you want to contact us about our services , you can find more details at www.itv.com/contactus",
              "Platonova 20b/112-1 E-mail : info @ saygames.by If you wish to make a complaint over the processing of your personal data , you have the right to lodge a complaint to the relevant supervisory authority"]

for text in list_of_texts:
    # text_as_list = list()
    # text_as_list.append(text)
    # tokenized_text = tokenizer.tokenize_text(text_as_list)
    # for bla in tokenized_text:
        # for token in bla:
        #    print("{}\t{}\t{}\t{}".format(token.text, token.token_class, token.extra_info, token.original_spelling))
    # print([detokenize(bla) for bla in tokenized_text][0])
    print(somajo_remove_url(text))
    print()
